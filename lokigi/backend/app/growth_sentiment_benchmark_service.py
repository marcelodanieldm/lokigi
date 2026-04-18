from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import (
    GrowthClientKeywordMetric,
    GrowthClientSnapshot,
    GrowthCompetitor,
    GrowthCompetitorKeywordMetric,
    GrowthCompetitorSnapshot,
    GrowthSentimentBenchmarkRun,
    GrowthSentimentBenchmarkTopicGap,
)


@dataclass
class BenchmarkConfig:
    time_window_days: int = 30
    min_support_topic_competitors: int = 30
    opp_threshold_competitor_complaint_rate: float = 0.35
    opp_threshold_client_complaint_rate: float = 0.15
    confidence_threshold: float = 0.70
    top_marketing_opportunities: int = 8


class GrowthSentimentBenchmarkService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_for_user(self, user_id: UUID, config: BenchmarkConfig | None = None) -> dict[str, Any]:
        cfg = config or BenchmarkConfig()
        now = datetime.now(timezone.utc)
        period_end = now.date()
        period_start = period_end - timedelta(days=max(cfg.time_window_days - 1, 0))

        competitors = self.db.scalars(
            select(GrowthCompetitor)
            .where(GrowthCompetitor.user_id == user_id, GrowthCompetitor.is_active.is_(True))
            .order_by(GrowthCompetitor.created_at.asc())
            .limit(5)
        ).all()

        client_snapshot = self.db.scalars(
            select(GrowthClientSnapshot)
            .where(GrowthClientSnapshot.user_id == user_id)
            .order_by(desc(GrowthClientSnapshot.observed_at))
            .limit(1)
        ).first()

        competitor_snapshots: dict[UUID, GrowthCompetitorSnapshot] = {}
        for competitor in competitors:
            snapshot = self.db.scalars(
                select(GrowthCompetitorSnapshot)
                .where(GrowthCompetitorSnapshot.competitor_id == competitor.id)
                .order_by(desc(GrowthCompetitorSnapshot.observed_at))
                .limit(1)
            ).first()
            if snapshot:
                competitor_snapshots[competitor.id] = snapshot

        brand_table: list[dict[str, Any]] = []

        client_score = self._rating_to_sentiment_score(
            float(client_snapshot.rating_avg) if client_snapshot and client_snapshot.rating_avg is not None else None
        )
        client_negative_rate = self._rating_to_negative_rate(
            float(client_snapshot.rating_avg) if client_snapshot and client_snapshot.rating_avg is not None else None
        )

        client_topic_negative = self._client_topic_negative_rates(user_id, period_start, period_end)
        competitor_topic_agg = self._competitor_topic_negative_rates(
            [c.id for c in competitors], period_start, period_end
        )

        # Build brand table with top critical topics for each brand.
        if client_snapshot:
            brand_table.append(
                {
                    "brand_id": str(user_id),
                    "brand_name": "Cliente",
                    "sentiment_score": client_score,
                    "negative_rate": client_negative_rate,
                    "volume": client_snapshot.review_count_total or 0,
                    "top_critical_topics": self._top_topics(client_topic_negative),
                }
            )

        competitor_scores: list[float] = []
        for competitor in competitors:
            snapshot = competitor_snapshots.get(competitor.id)
            rating_value = float(snapshot.rating_avg) if snapshot and snapshot.rating_avg is not None else None
            score = self._rating_to_sentiment_score(rating_value)
            negative = self._rating_to_negative_rate(rating_value)
            if score is not None:
                competitor_scores.append(score)

            topics_for_competitor = self._competitor_single_topic_negative_rates(
                competitor.id,
                period_start,
                period_end,
            )
            brand_table.append(
                {
                    "brand_id": str(competitor.id),
                    "brand_name": competitor.name,
                    "sentiment_score": score,
                    "negative_rate": negative,
                    "volume": snapshot.review_count_total if snapshot and snapshot.review_count_total else 0,
                    "top_critical_topics": self._top_topics(topics_for_competitor),
                }
            )

        competitor_average_score = round(sum(competitor_scores) / len(competitor_scores), 3) if competitor_scores else None

        ranking_pool = [
            score for score in [client_score, *competitor_scores] if score is not None
        ]
        rank_client = None
        if client_score is not None and ranking_pool:
            sorted_scores = sorted(ranking_pool, reverse=True)
            rank_client = sorted_scores.index(client_score) + 1

        topic_gaps = self._build_topic_gaps(
            client_topic_negative=client_topic_negative,
            competitor_topic_agg=competitor_topic_agg,
            cfg=cfg,
        )

        opportunities = [
            row
            for row in topic_gaps
            if row["label"] == "Oportunidad de Marketing"
        ][: cfg.top_marketing_opportunities]

        run_row = self._persist_run(
            user_id=user_id,
            cfg=cfg,
            client_score=client_score,
            competitor_average_score=competitor_average_score,
            client_negative_rate=client_negative_rate,
            rank_client=rank_client,
            summary_payload={
                "brand_table": brand_table,
                "topic_gaps": topic_gaps,
                "marketing_opportunities": opportunities,
            },
            diagnostics_payload={
                "competitors_considered": len(competitors),
                "period_start": str(period_start),
                "period_end": str(period_end),
            },
            topic_gaps=topic_gaps,
        )

        status = "ok" if competitors else "partial"
        if not competitors:
            status = "partial"

        payload = {
            "job_id": str(run_row.id),
            "status": status,
            "window": {
                "start_date": str(period_start),
                "end_date": str(period_end),
                "time_window_days": cfg.time_window_days,
            },
            "summary": {
                "client_sentiment_score": client_score,
                "client_negative_rate": client_negative_rate,
                "competitor_average_sentiment_score": competitor_average_score,
                "rank_client_among_6": rank_client,
            },
            "brand_table": brand_table,
            "topic_gaps": topic_gaps,
            "marketing_opportunities": opportunities,
            "diagnostics": {
                "docs_total_client": 0,
                "docs_total_competitors": 0,
                "docs_deduplicated": 0,
                "docs_filtered_spam": 0,
                "model_version": "v1-growth-sentiment-benchmark",
                "notes": [
                    "Current implementation uses persisted keyword metrics + latest snapshots.",
                    "If sentiment percentages are missing for keywords, rows are marked as No concluyente.",
                ],
            },
        }
        return payload

    def _persist_run(
        self,
        *,
        user_id: UUID,
        cfg: BenchmarkConfig,
        client_score: float | None,
        competitor_average_score: float | None,
        client_negative_rate: float | None,
        rank_client: int | None,
        summary_payload: dict[str, Any],
        diagnostics_payload: dict[str, Any],
        topic_gaps: list[dict[str, Any]],
    ) -> GrowthSentimentBenchmarkRun:
        run = GrowthSentimentBenchmarkRun(
            user_id=user_id,
            window_days=cfg.time_window_days,
            status="ok",
            client_sentiment_score=client_score,
            competitor_average_sentiment_score=competitor_average_score,
            client_negative_rate=client_negative_rate,
            rank_client_among_6=rank_client,
            summary_payload=summary_payload,
            diagnostics_payload=diagnostics_payload,
        )
        self.db.add(run)
        self.db.flush()

        for row in topic_gaps:
            self.db.add(
                GrowthSentimentBenchmarkTopicGap(
                    run_id=run.id,
                    user_id=user_id,
                    topic=row["topic"],
                    client_complaint_rate=row["client_complaint_rate"],
                    competitor_complaint_rate=row["competitor_complaint_rate"],
                    gap=row["gap"],
                    support_competitors=row["support_competitors"],
                    label=row["label"],
                    confidence=row["confidence"],
                    evidence_payload={
                        "marketing_label": row.get("marketing_label"),
                        "suggested_copy": row.get("suggested_copy"),
                        "risk_level": row.get("risk_level"),
                    },
                )
            )

        self.db.commit()
        self.db.refresh(run)
        return run

    def _build_topic_gaps(
        self,
        *,
        client_topic_negative: dict[str, tuple[float | None, int]],
        competitor_topic_agg: dict[str, tuple[float | None, int]],
        cfg: BenchmarkConfig,
    ) -> list[dict[str, Any]]:
        topics = sorted(set(client_topic_negative.keys()) | set(competitor_topic_agg.keys()))
        rows: list[dict[str, Any]] = []

        for topic in topics:
            client_rate, _ = client_topic_negative.get(topic, (None, 0))
            competitor_rate, support = competitor_topic_agg.get(topic, (None, 0))

            if client_rate is None or competitor_rate is None:
                rows.append(
                    {
                        "topic": topic,
                        "client_complaint_rate": client_rate,
                        "competitor_complaint_rate": competitor_rate,
                        "gap": None,
                        "support_competitors": support,
                        "label": "No concluyente",
                        "confidence": 0.0,
                    }
                )
                continue

            gap = round(competitor_rate - client_rate, 3)
            confidence = min(1.0, round(support / max(cfg.min_support_topic_competitors, 1), 3))

            label = "Paridad"
            marketing_label = None
            suggested_copy = None
            risk_level = None

            if (
                support >= cfg.min_support_topic_competitors
                and competitor_rate >= cfg.opp_threshold_competitor_complaint_rate
                and client_rate <= cfg.opp_threshold_client_complaint_rate
                and confidence >= cfg.confidence_threshold
            ):
                label = "Oportunidad de Marketing"
                marketing_label = self._marketing_label_for_topic(topic)
                suggested_copy = self._suggested_copy_for_topic(topic)
                risk_level = "bajo"
            elif gap < -0.05:
                label = "Desventaja"

            rows.append(
                {
                    "topic": topic,
                    "client_complaint_rate": round(client_rate, 3),
                    "competitor_complaint_rate": round(competitor_rate, 3),
                    "gap": gap,
                    "support_competitors": support,
                    "label": label,
                    "confidence": confidence,
                    "marketing_label": marketing_label,
                    "suggested_copy": suggested_copy,
                    "risk_level": risk_level,
                }
            )

        rows.sort(
            key=lambda item: (
                0 if item["label"] == "Oportunidad de Marketing" else 1,
                -(item["gap"] if isinstance(item.get("gap"), (float, int)) else -999),
            )
        )
        return rows

    def _client_topic_negative_rates(
        self,
        user_id: UUID,
        period_start,
        period_end,
    ) -> dict[str, tuple[float | None, int]]:
        rows = self.db.scalars(
            select(GrowthClientKeywordMetric).where(
                GrowthClientKeywordMetric.user_id == user_id,
                GrowthClientKeywordMetric.period_start == period_start,
                GrowthClientKeywordMetric.period_end == period_end,
            )
        ).all()

        out: dict[str, tuple[float | None, int]] = {}
        for row in rows:
            negative_pct = float(row.sentiment_negative_pct) / 100 if row.sentiment_negative_pct is not None else None
            out[row.keyword] = (negative_pct, row.mentions_count)
        return out

    def _competitor_single_topic_negative_rates(
        self,
        competitor_id: UUID,
        period_start,
        period_end,
    ) -> dict[str, tuple[float | None, int]]:
        rows = self.db.scalars(
            select(GrowthCompetitorKeywordMetric).where(
                GrowthCompetitorKeywordMetric.competitor_id == competitor_id,
                GrowthCompetitorKeywordMetric.period_start == period_start,
                GrowthCompetitorKeywordMetric.period_end == period_end,
            )
        ).all()

        out: dict[str, tuple[float | None, int]] = {}
        for row in rows:
            negative_pct = float(row.sentiment_negative_pct) / 100 if row.sentiment_negative_pct is not None else None
            out[row.keyword] = (negative_pct, row.mentions_count)
        return out

    def _competitor_topic_negative_rates(
        self,
        competitor_ids: list[UUID],
        period_start,
        period_end,
    ) -> dict[str, tuple[float | None, int]]:
        if not competitor_ids:
            return {}

        rows = self.db.scalars(
            select(GrowthCompetitorKeywordMetric).where(
                GrowthCompetitorKeywordMetric.competitor_id.in_(competitor_ids),
                GrowthCompetitorKeywordMetric.period_start == period_start,
                GrowthCompetitorKeywordMetric.period_end == period_end,
            )
        ).all()

        bucket: dict[str, list[tuple[float, int]]] = {}
        support: dict[str, int] = {}
        for row in rows:
            support[row.keyword] = support.get(row.keyword, 0) + (row.mentions_count or 0)
            if row.sentiment_negative_pct is None:
                continue
            bucket.setdefault(row.keyword, []).append(
                (float(row.sentiment_negative_pct) / 100, row.mentions_count or 0)
            )

        out: dict[str, tuple[float | None, int]] = {}
        for topic in set(list(bucket.keys()) + list(support.keys())):
            series = bucket.get(topic, [])
            if not series:
                out[topic] = (None, support.get(topic, 0))
                continue
            total_weight = sum(weight for _, weight in series) or len(series)
            weighted = sum(value * (weight or 1) for value, weight in series) / total_weight
            out[topic] = (weighted, support.get(topic, 0))
        return out

    def _top_topics(self, topic_rates: dict[str, tuple[float | None, int]]) -> list[str]:
        ranked = sorted(
            topic_rates.items(),
            key=lambda item: (
                (item[1][0] if item[1][0] is not None else -1),
                item[1][1],
            ),
            reverse=True,
        )
        return [topic for topic, _ in ranked[:3]]

    def _rating_to_sentiment_score(self, rating: float | None) -> float | None:
        if rating is None:
            return None
        # Map 1-5 to -1..1
        score = (rating - 3.0) / 2.0
        return round(max(-1.0, min(1.0, score)), 3)

    def _rating_to_negative_rate(self, rating: float | None) -> float | None:
        if rating is None:
            return None
        # Simple monotonic approximation for dashboard baseline.
        neg = max(0.0, min(1.0, (5.0 - rating) / 4.0))
        return round(neg, 3)

    def _marketing_label_for_topic(self, topic: str) -> str:
        mapping = {
            "tiempo de espera": "Rapidez comprobada",
            "espera": "Rapidez comprobada",
            "demora": "Rapidez comprobada",
            "precio": "Valor competitivo",
            "atencion": "Atencion destacada",
        }
        return mapping.get(topic.lower(), f"Fortaleza en {topic}")

    def _suggested_copy_for_topic(self, topic: str) -> str:
        if topic.lower() in {"tiempo de espera", "espera", "demora"}:
            return "Atencion agil y tiempos de espera minimos para resolverte rapido."
        if topic.lower() == "precio":
            return "Precios claros y una relacion valor-servicio que nuestros clientes destacan."
        return f"Clientes destacan nuestra fortaleza en {topic}, con experiencia consistente y confiable."
