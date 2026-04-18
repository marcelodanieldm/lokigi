from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.google_client import GoogleBusinessProfileClient, GoogleOAuthError
from app.models import (
    GoogleConnection,
    GrowthClientKeywordMetric,
    GrowthCompetitor,
    GrowthCompetitorKeywordMetric,
    GrowthSeoAlert,
    GrowthSeoSuggestion,
    GrowthSeoSuggestionAction,
)
from app.services import ensure_valid_access_token


@dataclass
class SeoConfig:
    max_active_per_type: int = 3
    min_support: int = 10
    min_gap_share: float = 0.01
    high_priority_threshold: int = 75


class GrowthSeoService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_or_generate_suggestions(self, user_id: UUID, force_refresh: bool = False) -> list[GrowthSeoSuggestion]:
        active = self._active_suggestions(user_id)
        if active and not force_refresh:
            return active

        if force_refresh and active:
            now = datetime.now(timezone.utc)
            for row in active:
                row.status = "deprecated"
                row.updated_at = now
                self.db.add(row)
            self.db.commit()

        generated = self._generate_suggestions(user_id)
        return generated if generated else self._active_suggestions(user_id)

    async def apply_suggestion(self, user_id: UUID, suggestion_id: UUID) -> dict[str, Any]:
        suggestion = self.db.get(GrowthSeoSuggestion, suggestion_id)
        if not suggestion or suggestion.user_id != user_id:
            raise ValueError("Suggestion not found")

        if suggestion.status == "applied":
            return {
                "already_applied": True,
                "suggestion_id": str(suggestion.id),
                "status": suggestion.status,
            }

        connection = self.db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
        if not connection:
            raise ValueError("Google connection not found")

        location_name = f"{connection.google_account_name}/locations/{connection.location_id}"
        access_token = await ensure_valid_access_token(self.db, connection)
        client = GoogleBusinessProfileClient(
            settings.google_client_id,
            settings.google_client_secret,
            settings.google_redirect_uri,
        )

        try:
            google_response = await client.update_location_description(
                access_token=access_token,
                location_name=location_name,
                description=suggestion.suggested_text,
            )
        except GoogleOAuthError as exc:
            self._create_action(
                suggestion=suggestion,
                action_type="apply",
                status="error",
                request_payload={"mode": suggestion.suggestion_type, "suggested_text": suggestion.suggested_text},
                response_payload={"error": str(exc)},
            )
            self.db.commit()
            raise RuntimeError(str(exc)) from exc

        now = datetime.now(timezone.utc)
        suggestion.status = "applied"
        suggestion.applied_at = now
        suggestion.updated_at = now
        self.db.add(suggestion)

        self._create_action(
            suggestion=suggestion,
            action_type="apply",
            status="ok",
            request_payload={
                "mode": suggestion.suggestion_type,
                "location_name": location_name,
                "suggested_text": suggestion.suggested_text,
            },
            response_payload=google_response,
        )

        # Mark related alerts as seen after applying.
        alerts = self.db.scalars(
            select(GrowthSeoAlert).where(
                GrowthSeoAlert.user_id == user_id,
                GrowthSeoAlert.suggestion_id == suggestion.id,
                GrowthSeoAlert.is_seen.is_(False),
            )
        ).all()
        for alert in alerts:
            alert.is_seen = True
            alert.seen_at = now
            self.db.add(alert)

        self.db.commit()
        return {
            "already_applied": False,
            "suggestion_id": str(suggestion.id),
            "status": suggestion.status,
            "google_response": google_response,
        }

    def dismiss_suggestion(self, user_id: UUID, suggestion_id: UUID, reason: str | None = None) -> dict[str, Any]:
        suggestion = self.db.get(GrowthSeoSuggestion, suggestion_id)
        if not suggestion or suggestion.user_id != user_id:
            raise ValueError("Suggestion not found")

        if suggestion.status in {"dismissed", "applied"}:
            return {
                "already_closed": True,
                "suggestion_id": str(suggestion.id),
                "status": suggestion.status,
            }

        now = datetime.now(timezone.utc)
        suggestion.status = "dismissed"
        suggestion.dismissed_at = now
        suggestion.updated_at = now
        self.db.add(suggestion)

        self._create_action(
            suggestion=suggestion,
            action_type="dismiss",
            status="ok",
            request_payload={"reason": reason or "manual"},
            response_payload={},
        )

        alerts = self.db.scalars(
            select(GrowthSeoAlert).where(
                GrowthSeoAlert.user_id == user_id,
                GrowthSeoAlert.suggestion_id == suggestion.id,
                GrowthSeoAlert.is_seen.is_(False),
            )
        ).all()
        for alert in alerts:
            alert.is_seen = True
            alert.seen_at = now
            self.db.add(alert)

        self.db.commit()
        return {
            "already_closed": False,
            "suggestion_id": str(suggestion.id),
            "status": suggestion.status,
        }

    def list_alerts(self, user_id: UUID, mark_seen: bool = False) -> list[GrowthSeoAlert]:
        alerts = self.db.scalars(
            select(GrowthSeoAlert)
            .where(GrowthSeoAlert.user_id == user_id)
            .order_by(desc(GrowthSeoAlert.created_at))
            .limit(50)
        ).all()

        if mark_seen:
            now = datetime.now(timezone.utc)
            for alert in alerts:
                if not alert.is_seen:
                    alert.is_seen = True
                    alert.seen_at = now
                    self.db.add(alert)
            self.db.commit()

        return alerts

    def _active_suggestions(self, user_id: UUID) -> list[GrowthSeoSuggestion]:
        return list(
            self.db.scalars(
                select(GrowthSeoSuggestion)
                .where(
                    GrowthSeoSuggestion.user_id == user_id,
                    GrowthSeoSuggestion.status == "active",
                )
                .order_by(desc(GrowthSeoSuggestion.priority_score), GrowthSeoSuggestion.created_at.desc())
                .limit(12)
            ).all()
        )

    def _generate_suggestions(self, user_id: UUID) -> list[GrowthSeoSuggestion]:
        cfg = SeoConfig()
        latest_period = self.db.execute(
            select(GrowthClientKeywordMetric.period_start, GrowthClientKeywordMetric.period_end)
            .where(GrowthClientKeywordMetric.user_id == user_id)
            .order_by(desc(GrowthClientKeywordMetric.period_end))
            .limit(1)
        ).first()
        if not latest_period:
            return []

        period_start, period_end = latest_period
        client_rows = self.db.scalars(
            select(GrowthClientKeywordMetric).where(
                GrowthClientKeywordMetric.user_id == user_id,
                GrowthClientKeywordMetric.period_start == period_start,
                GrowthClientKeywordMetric.period_end == period_end,
            )
        ).all()

        competitor_ids = self.db.scalars(
            select(GrowthCompetitor.id).where(
                GrowthCompetitor.user_id == user_id,
                GrowthCompetitor.is_active.is_(True),
            )
        ).all()
        if not competitor_ids:
            return []

        competitor_rows = self.db.scalars(
            select(GrowthCompetitorKeywordMetric).where(
                GrowthCompetitorKeywordMetric.competitor_id.in_(competitor_ids),
                GrowthCompetitorKeywordMetric.period_start == period_start,
                GrowthCompetitorKeywordMetric.period_end == period_end,
            )
        ).all()

        client_mentions: dict[str, int] = {}
        total_client_mentions = 0
        for row in client_rows:
            key = row.keyword.lower().strip()
            client_mentions[key] = client_mentions.get(key, 0) + int(row.mentions_count or 0)
            total_client_mentions += int(row.mentions_count or 0)

        competitor_mentions: dict[str, int] = {}
        for row in competitor_rows:
            key = row.keyword.lower().strip()
            competitor_mentions[key] = competitor_mentions.get(key, 0) + int(row.mentions_count or 0)
        total_comp_mentions = sum(competitor_mentions.values())

        if total_comp_mentions == 0:
            return []

        candidates: list[dict[str, Any]] = []
        for keyword, comp_count in competitor_mentions.items():
            support = comp_count
            if support < cfg.min_support or len(keyword) < 3:
                continue

            client_count = client_mentions.get(keyword, 0)
            comp_share = comp_count / max(total_comp_mentions, 1)
            client_share = client_count / max(total_client_mentions, 1) if total_client_mentions else 0.0
            gap_share = comp_share - client_share
            if gap_share < cfg.min_gap_share:
                continue

            confidence = min(1.0, support / 60)
            priority = int(min(100, (gap_share * 500) + min(30, support / 3) + confidence * 20))
            risk = "bajo" if priority >= 70 else "medio"

            candidates.append(
                {
                    "keyword": keyword,
                    "support": support,
                    "comp_share": round(comp_share, 4),
                    "client_share": round(client_share, 4),
                    "gap_share": round(gap_share, 4),
                    "confidence": round(confidence, 3),
                    "priority": priority,
                    "risk": risk,
                }
            )

        candidates.sort(key=lambda item: (item["priority"], item["gap_share"], item["support"]), reverse=True)

        connection = self.db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
        current_description = connection.business_name if connection and connection.business_name else ""

        created: list[GrowthSeoSuggestion] = []
        count_by_type = {"description_update": 0, "service_update": 0}
        now = datetime.now(timezone.utc)

        for item in candidates:
            suggestion_type = "description_update" if count_by_type["description_update"] <= count_by_type["service_update"] else "service_update"
            if count_by_type[suggestion_type] >= cfg.max_active_per_type:
                alternative = "service_update" if suggestion_type == "description_update" else "description_update"
                if count_by_type[alternative] >= cfg.max_active_per_type:
                    continue
                suggestion_type = alternative

            suggested_text = self._build_suggested_text(
                current_description=current_description,
                keyword=item["keyword"],
                suggestion_type=suggestion_type,
            )

            suggestion = GrowthSeoSuggestion(
                user_id=user_id,
                suggestion_type=suggestion_type,
                keyword=item["keyword"],
                current_text=current_description,
                suggested_text=suggested_text,
                keywords_payload={"primary": item["keyword"]},
                justification_payload={
                    "support": item["support"],
                    "comp_share": item["comp_share"],
                    "client_share": item["client_share"],
                    "gap_share": item["gap_share"],
                    "confidence": item["confidence"],
                },
                risk_level=item["risk"],
                priority_score=item["priority"],
                source_period_start=period_start,
                source_period_end=period_end,
                status="active",
                created_at=now,
                updated_at=now,
            )
            self.db.add(suggestion)
            self.db.flush()
            created.append(suggestion)
            count_by_type[suggestion_type] += 1

            if item["priority"] >= cfg.high_priority_threshold:
                self.db.add(
                    GrowthSeoAlert(
                        user_id=user_id,
                        suggestion_id=suggestion.id,
                        title="Nueva oportunidad SEO detectada",
                        message=(
                            f"La keyword '{item['keyword']}' muestra gap de mercado "
                            f"({item['gap_share']:.2%}) frente a competencia."
                        ),
                        severity="high",
                        is_seen=False,
                    )
                )

            if count_by_type["description_update"] >= cfg.max_active_per_type and count_by_type["service_update"] >= cfg.max_active_per_type:
                break

        self.db.commit()
        return created

    def _build_suggested_text(self, *, current_description: str, keyword: str, suggestion_type: str) -> str:
        base = (current_description or "").strip()
        safe_keyword = keyword.strip().lower()

        if suggestion_type == "description_update":
            if safe_keyword in base.lower():
                return base
            extension = f" Destacamos {safe_keyword} con atencion profesional y resultados consistentes."
            return (base + extension).strip()[:740]

        # service_update is represented as a service-line insertion in profile description
        service_line = f"Servicios destacados: {safe_keyword}."
        if service_line.lower() in base.lower():
            return base
        return (base + " " + service_line).strip()[:740]

    def _create_action(
        self,
        *,
        suggestion: GrowthSeoSuggestion,
        action_type: str,
        status: str,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
    ) -> None:
        self.db.add(
            GrowthSeoSuggestionAction(
                suggestion_id=suggestion.id,
                user_id=suggestion.user_id,
                action_type=action_type,
                status=status,
                request_payload=request_payload,
                response_payload=response_payload,
            )
        )
