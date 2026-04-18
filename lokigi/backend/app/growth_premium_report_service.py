from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .models import (
    GrowthClientServiceSnapshot,
    GrowthClientSnapshot,
    GrowthCompetitor,
    GrowthCompetitorServiceSnapshot,
    GrowthCompetitorSnapshot,
    GrowthKeywordConquestEvent,
    GrowthSentimentBenchmarkRun,
    GrowthSerpObservation,
    MonthlyReport,
)


@dataclass
class PremiumConfig:
    window_days: int = 30
    max_locations: int = 5


class GrowthPremiumReportService:
    def __init__(self, db: Session):
        self.db = db

    def build_report(self, user_id: UUID, config: PremiumConfig) -> dict:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=config.window_days)

        msp = self._compute_market_share_pack(user_id=user_id, cutoff=cutoff)
        conquest = self._compute_keyword_conquest_rate(user_id=user_id, cutoff=cutoff)
        sentiment_delta = self._compute_competitor_sentiment_delta(user_id=user_id)
        avi = self._compute_activity_velocity_index(user_id=user_id, cutoff=cutoff)
        service_gap = self._compute_service_gap_analysis(user_id=user_id)
        multi_location = self._build_multi_location_breakdown(
            user_id=user_id,
            cutoff=cutoff,
            max_locations=config.max_locations,
        )

        change_of_guard = self._detect_change_of_guard(user_id=user_id, config=config, current_msp=msp)
        threat_detected = self._detect_threat_detected(current_avi=avi, sentiment_delta=sentiment_delta)
        local_dominance = self._build_local_dominance_state(
            multi_location=multi_location,
            change_of_guard=change_of_guard,
            threat_detected=threat_detected,
        )
        roi_evolution = self._compute_roi_evolution(user_id=user_id)

        return {
            "window_days": config.window_days,
            "max_locations": config.max_locations,
            "generated_at": now.isoformat(),
            "kpis": {
                "market_share_pack_pct": msp,
                "keyword_conquest_rate_pct": conquest,
                "competitor_sentiment_delta": sentiment_delta,
                "activity_velocity_index": avi,
            },
            "analysis": {
                "service_gap_opportunities": service_gap,
                "multi_location": multi_location,
                "local_dominance_state": local_dominance,
            },
            "alerts": {
                "change_of_guard": change_of_guard,
                "threat_detected": threat_detected,
            },
            "roi": roi_evolution,
            "prompts": self._build_prompts_payload(),
        }

    def _compute_market_share_pack(self, user_id: UUID, cutoff: datetime) -> float | None:
        rows = self.db.scalars(
            select(GrowthSerpObservation)
            .where(
                GrowthSerpObservation.user_id == user_id,
                GrowthSerpObservation.observed_at >= cutoff,
            )
            .order_by(GrowthSerpObservation.observed_at.asc())
        ).all()
        if not rows:
            return None

        grouped: dict[tuple[str, str, datetime], list[GrowthSerpObservation]] = defaultdict(list)
        for row in rows:
            grouped[(row.keyword, row.location_label, row.observed_at)].append(row)

        total_serps = 0
        client_top3 = 0
        for serp_rows in grouped.values():
            top3 = sorted(serp_rows, key=lambda x: x.rank_position)[:3]
            total_serps += 1
            if any(r.entity_type == "client" for r in top3):
                client_top3 += 1

        if total_serps == 0:
            return None
        return round((client_top3 / total_serps) * 100.0, 2)

    def _compute_keyword_conquest_rate(self, user_id: UUID, cutoff: datetime) -> float | None:
        conquests = self.db.scalars(
            select(GrowthKeywordConquestEvent).where(
                GrowthKeywordConquestEvent.user_id == user_id,
                GrowthKeywordConquestEvent.conquered_at >= cutoff,
            )
        ).all()

        strategic_keywords = self.db.scalars(
            select(GrowthSerpObservation.keyword)
            .where(
                GrowthSerpObservation.user_id == user_id,
                GrowthSerpObservation.entity_type == "client",
                GrowthSerpObservation.observed_at >= cutoff,
            )
            .distinct()
        ).all()

        denominator = len(strategic_keywords)
        if denominator == 0:
            return None
        return round((len(conquests) / denominator) * 100.0, 2)

    def _compute_competitor_sentiment_delta(self, user_id: UUID) -> float | None:
        run = self.db.scalars(
            select(GrowthSentimentBenchmarkRun)
            .where(GrowthSentimentBenchmarkRun.user_id == user_id)
            .order_by(desc(GrowthSentimentBenchmarkRun.created_at))
            .limit(1)
        ).first()
        if not run:
            return None
        if run.client_sentiment_score is None or run.competitor_average_sentiment_score is None:
            return None
        return round(float(run.client_sentiment_score) - float(run.competitor_average_sentiment_score), 4)

    def _compute_activity_velocity_index(self, user_id: UUID, cutoff: datetime) -> float | None:
        client_snapshot = self.db.scalars(
            select(GrowthClientSnapshot)
            .where(
                GrowthClientSnapshot.user_id == user_id,
                GrowthClientSnapshot.observed_at >= cutoff,
            )
            .order_by(desc(GrowthClientSnapshot.observed_at))
            .limit(1)
        ).first()
        if not client_snapshot:
            return None

        competitors = self.db.scalars(
            select(GrowthCompetitor)
            .where(
                GrowthCompetitor.user_id == user_id,
                GrowthCompetitor.is_active.is_(True),
            )
        ).all()
        if not competitors:
            return None

        competitor_scores: list[float] = []
        for comp in competitors:
            snap = self.db.scalars(
                select(GrowthCompetitorSnapshot)
                .where(
                    GrowthCompetitorSnapshot.competitor_id == comp.id,
                    GrowthCompetitorSnapshot.observed_at >= cutoff,
                )
                .order_by(desc(GrowthCompetitorSnapshot.observed_at))
                .limit(1)
            ).first()
            if not snap:
                continue
            competitor_scores.append(self._activity_score(snap.posts_count_30d, snap.photos_count_total))

        if not competitor_scores:
            return None

        client_score = self._activity_score(client_snapshot.posts_count_30d, client_snapshot.photos_count_total)
        baseline = mean(competitor_scores)
        if baseline <= 0:
            return None

        return round(client_score / baseline, 3)

    def _activity_score(self, posts_30d: int | None, photos_total: int | None) -> float:
        posts = float(posts_30d or 0)
        photos = float(photos_total or 0)
        return (posts * 0.7) + (photos * 0.3)

    def _compute_service_gap_analysis(self, user_id: UUID) -> list[dict]:
        competitors = self.db.scalars(
            select(GrowthCompetitor)
            .where(
                GrowthCompetitor.user_id == user_id,
                GrowthCompetitor.is_active.is_(True),
            )
        ).all()
        if not competitors:
            return []

        client_snapshot = self.db.scalars(
            select(GrowthClientSnapshot)
            .where(GrowthClientSnapshot.user_id == user_id)
            .order_by(desc(GrowthClientSnapshot.observed_at))
            .limit(1)
        ).first()
        if not client_snapshot:
            return []

        client_services = set(
            self.db.scalars(
                select(GrowthClientServiceSnapshot.service_name_normalized).where(
                    GrowthClientServiceSnapshot.user_id == user_id,
                    GrowthClientServiceSnapshot.observed_at == client_snapshot.observed_at,
                )
            ).all()
        )

        counts: dict[str, int] = defaultdict(int)
        exemplars: dict[str, list[str]] = defaultdict(list)
        for comp in competitors:
            comp_snapshot = self.db.scalars(
                select(GrowthCompetitorSnapshot)
                .where(GrowthCompetitorSnapshot.competitor_id == comp.id)
                .order_by(desc(GrowthCompetitorSnapshot.observed_at))
                .limit(1)
            ).first()
            if not comp_snapshot:
                continue

            comp_services = set(
                self.db.scalars(
                    select(GrowthCompetitorServiceSnapshot.service_name_normalized).where(
                        GrowthCompetitorServiceSnapshot.competitor_id == comp.id,
                        GrowthCompetitorServiceSnapshot.observed_at == comp_snapshot.observed_at,
                    )
                ).all()
            )
            for service in comp_services:
                if service in client_services:
                    continue
                counts[service] += 1
                if len(exemplars[service]) < 3:
                    exemplars[service].append(comp.name)

        opportunities = [
            {
                "service": service,
                "supporting_competitors": support,
                "examples": exemplars.get(service, []),
                "recommendation": f"Evaluar incorporacion de '{service}' en la ficha y operativa.",
            }
            for service, support in counts.items()
            if support >= 3
        ]
        opportunities.sort(key=lambda row: row["supporting_competitors"], reverse=True)
        return opportunities

    def _build_multi_location_breakdown(
        self,
        user_id: UUID,
        cutoff: datetime,
        max_locations: int,
    ) -> dict:
        rows = self.db.scalars(
            select(GrowthSerpObservation)
            .where(
                GrowthSerpObservation.user_id == user_id,
                GrowthSerpObservation.observed_at >= cutoff,
            )
            .order_by(GrowthSerpObservation.observed_at.asc())
        ).all()
        if not rows:
            return {
                "items": [],
                "location_count_total": 0,
            }

        conquest_rows = self.db.scalars(
            select(GrowthKeywordConquestEvent)
            .where(
                GrowthKeywordConquestEvent.user_id == user_id,
                GrowthKeywordConquestEvent.conquered_at >= cutoff,
            )
            .order_by(GrowthKeywordConquestEvent.conquered_at.asc())
        ).all()

        location_groups: dict[str, list[GrowthSerpObservation]] = defaultdict(list)
        for row in rows:
            label = (row.location_label or "default").strip().lower()
            location_groups[label].append(row)

        conquest_by_location: dict[str, list[GrowthKeywordConquestEvent]] = defaultdict(list)
        for event in conquest_rows:
            label = (event.location_label or "default").strip().lower()
            conquest_by_location[label].append(event)

        items: list[dict] = []
        for label, location_rows in location_groups.items():
            serp_groups: dict[tuple[str, datetime], list[GrowthSerpObservation]] = defaultdict(list)
            for row in location_rows:
                serp_groups[(row.keyword, row.observed_at)].append(row)

            total_serps = 0
            client_top3 = 0
            for serp_rows in serp_groups.values():
                top3 = sorted(serp_rows, key=lambda x: x.rank_position)[:3]
                total_serps += 1
                if any(r.entity_type == "client" for r in top3):
                    client_top3 += 1

            msp = round((client_top3 / total_serps) * 100.0, 2) if total_serps else None

            client_rows = [row for row in location_rows if row.entity_type == "client"]
            avg_client_rank = (
                round(mean([float(row.rank_position) for row in client_rows]), 2)
                if client_rows
                else None
            )

            strategic_keywords = {row.keyword for row in client_rows if row.keyword}
            conquests = conquest_by_location.get(label, [])
            conquest_rate = (
                round((len(conquests) / len(strategic_keywords)) * 100.0, 2)
                if strategic_keywords
                else None
            )

            keyword_rank_map: dict[str, list[int]] = defaultdict(list)
            for row in client_rows:
                keyword_rank_map[row.keyword].append(row.rank_position)

            heatmap = [
                {
                    "keyword": keyword,
                    "avg_rank": round(mean([float(v) for v in ranks]), 2),
                    "status": "strong" if mean(ranks) <= 3 else ("watch" if mean(ranks) <= 7 else "weak"),
                }
                for keyword, ranks in keyword_rank_map.items()
            ]
            heatmap.sort(key=lambda row: row["avg_rank"])

            momentum_score = self._build_location_momentum_score(
                msp=msp,
                conquest_rate=conquest_rate,
                avg_rank=avg_client_rank,
            )

            items.append(
                {
                    "location_label": label,
                    "market_share_pack_pct": msp,
                    "keyword_conquest_rate_pct": conquest_rate,
                    "avg_client_rank": avg_client_rank,
                    "serp_samples": total_serps,
                    "conquests": len(conquests),
                    "momentum_score": momentum_score,
                    "keyword_heatmap": heatmap[:8],
                }
            )

        items.sort(
            key=lambda row: (
                row.get("momentum_score") is None,
                -(row.get("momentum_score") or 0),
                -(row.get("serp_samples") or 0),
            )
        )
        return {
            "items": items[:max_locations],
            "location_count_total": len(items),
        }

    def _build_location_momentum_score(
        self,
        msp: float | None,
        conquest_rate: float | None,
        avg_rank: float | None,
    ) -> float | None:
        if msp is None and conquest_rate is None and avg_rank is None:
            return None

        msp_component = (msp or 0.0) * 0.5
        conquest_component = (conquest_rate or 0.0) * 0.3
        rank_component = 0.0
        if avg_rank is not None:
            rank_component = max(0.0, (11.0 - avg_rank)) * (20.0 / 11.0)

        return round(msp_component + conquest_component + rank_component, 2)

    def _build_local_dominance_state(
        self,
        multi_location: dict,
        change_of_guard: dict,
        threat_detected: dict,
    ) -> dict:
        items = list(multi_location.get("items") or [])
        if not items:
            return {
                "status": "insufficient_data",
                "title": "Estado de Dominio Local",
                "message": "No hay datos suficientes de SERP por sede para calcular dominio.",
            }

        winner = sorted(items, key=lambda row: (row.get("momentum_score") or -1), reverse=True)[0]
        weak_locations = [
            row for row in items
            if (row.get("market_share_pack_pct") or 0) < 35
            or (row.get("avg_client_rank") or 99) > 7
        ]

        state = "dominant"
        if weak_locations or bool(change_of_guard.get("triggered")) or bool(threat_detected.get("triggered")):
            state = "contested"
        if len(weak_locations) >= max(1, len(items) // 2):
            state = "under_attack"

        action = (
            f"Replicar playbook de '{winner.get('location_label')}' en sedes con MSP bajo y reforzar keywords de baja posicion."
        )

        return {
            "status": state,
            "title": "Estado de Dominio Local",
            "winner": {
                "location_label": winner.get("location_label"),
                "momentum_score": winner.get("momentum_score"),
                "market_share_pack_pct": winner.get("market_share_pack_pct"),
            },
            "weak_locations": [row.get("location_label") for row in weak_locations[:5]],
            "change_of_guard_triggered": bool(change_of_guard.get("triggered")),
            "threat_detected_triggered": bool(threat_detected.get("triggered")),
            "recommended_action": action,
            "heatmap": [
                {
                    "location_label": row.get("location_label"),
                    "market_share_pack_pct": row.get("market_share_pack_pct"),
                    "avg_client_rank": row.get("avg_client_rank"),
                    "band": "high"
                    if (row.get("market_share_pack_pct") or 0) >= 60
                    else ("mid" if (row.get("market_share_pack_pct") or 0) >= 35 else "low"),
                }
                for row in items
            ],
        }

    def _detect_change_of_guard(
        self,
        user_id: UUID,
        config: PremiumConfig,
        current_msp: float | None,
    ) -> dict:
        if current_msp is None:
            return {"triggered": False, "reason": "insufficient_data"}

        now = datetime.now(timezone.utc)
        past_cutoff = now - timedelta(days=config.window_days * 2)
        middle_cutoff = now - timedelta(days=config.window_days)

        rows = self.db.scalars(
            select(GrowthSerpObservation)
            .where(
                GrowthSerpObservation.user_id == user_id,
                GrowthSerpObservation.observed_at >= past_cutoff,
                GrowthSerpObservation.observed_at < middle_cutoff,
            )
            .order_by(GrowthSerpObservation.observed_at.asc())
        ).all()
        if not rows:
            return {"triggered": False, "reason": "no_previous_window"}

        grouped: dict[tuple[str, str, datetime], list[GrowthSerpObservation]] = defaultdict(list)
        for row in rows:
            grouped[(row.keyword, row.location_label, row.observed_at)].append(row)

        previous_total = 0
        previous_client_top3 = 0
        for serp_rows in grouped.values():
            top3 = sorted(serp_rows, key=lambda x: x.rank_position)[:3]
            previous_total += 1
            if any(r.entity_type == "client" for r in top3):
                previous_client_top3 += 1

        if previous_total == 0:
            return {"triggered": False, "reason": "no_previous_window"}

        previous_msp = round((previous_client_top3 / previous_total) * 100.0, 2)
        drop = round(previous_msp - current_msp, 2)
        triggered = drop >= 8.0
        return {
            "triggered": triggered,
            "current_msp_pct": current_msp,
            "previous_msp_pct": previous_msp,
            "drop_pct_points": drop,
            "severity": "high" if drop >= 12 else "medium",
            "title": "Cambio de Guardia" if triggered else None,
        }

    def _detect_threat_detected(self, current_avi: float | None, sentiment_delta: float | None) -> dict:
        if current_avi is None or sentiment_delta is None:
            return {"triggered": False, "reason": "insufficient_data"}

        triggered = current_avi < 0.85 and sentiment_delta < 0
        return {
            "triggered": triggered,
            "activity_velocity_index": current_avi,
            "competitor_sentiment_delta": sentiment_delta,
            "severity": "high" if triggered else "info",
            "title": "Amenaza Detectada" if triggered else None,
        }

    def _compute_roi_evolution(self, user_id: UUID) -> dict:
        rows = self.db.scalars(
            select(MonthlyReport)
            .where(MonthlyReport.user_id == user_id)
            .order_by(MonthlyReport.year.asc(), MonthlyReport.month.asc())
        ).all()
        if len(rows) < 2:
            return {
                "has_history": False,
                "message": "No hay suficiente historial para comparar ROI antes vs hoy.",
            }

        first_payload = rows[0].payload or {}
        latest_payload = rows[-1].payload or {}

        first_rating = (first_payload.get("kpis") or {}).get("avg_rating")
        latest_rating = (latest_payload.get("kpis") or {}).get("avg_rating")
        first_response_rate = (first_payload.get("kpis") or {}).get("response_rate_pct")
        latest_response_rate = (latest_payload.get("kpis") or {}).get("response_rate_pct")

        def delta(a: float | None, b: float | None) -> float | None:
            if a is None or b is None:
                return None
            return round(float(b) - float(a), 2)

        return {
            "has_history": True,
            "before": {
                "year": rows[0].year,
                "month": rows[0].month,
                "avg_rating": first_rating,
                "response_rate_pct": first_response_rate,
            },
            "today": {
                "year": rows[-1].year,
                "month": rows[-1].month,
                "avg_rating": latest_rating,
                "response_rate_pct": latest_response_rate,
            },
            "delta": {
                "avg_rating": delta(first_rating, latest_rating),
                "response_rate_pct": delta(first_response_rate, latest_response_rate),
            },
        }

    def _build_prompts_payload(self) -> dict:
        return {
            "prompt_a": "Correlacion entre actividad de contenido competidor y posicion del cliente en ranking local.",
            "prompt_b": "Analisis de brecha de servicios: detectar servicios ofertados por >=3 competidores que el cliente no declara.",
            "prompt_c": "Reporte multiubicacion (hasta 5): contrastar KPIs por sede y resaltar la de mejor momentum.",
            "prompt_d": "Estado de dominio local: definir lider, amenazas y accion inmediata por categoria.",
        }
