from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.growth_event_notification_service import GrowthEventNotificationService
from app.growth_seo_service import GrowthSeoService
from app.models import (
    GrowthCompetitor,
    GrowthCompetitorKeywordMetric,
    GrowthKeywordConquestEvent,
    GrowthSerpObservation,
    StarterProfileSettings,
    User,
)


_PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"
_PLACES_NEARBY = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


class GrowthKeywordConquestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def run_daily_tracking(self) -> dict[str, int]:
        rows = self.db.execute(
            select(User.id, StarterProfileSettings.focus_keywords, StarterProfileSettings.client_google_place_id)
            .join(StarterProfileSettings, StarterProfileSettings.user_id == User.id)
            .where(StarterProfileSettings.focus_keywords.is_not(None))
        ).all()

        totals = {
            "processed_users": 0,
            "observations_inserted": 0,
            "conquests_inserted": 0,
            "suggestions_created": 0,
        }

        for user_id, focus_keywords, client_google_place_id in rows:
            keywords = self._normalize_keywords(focus_keywords)
            if not client_google_place_id or not keywords:
                continue
            summary = await self.track_user(user_id=user_id, client_google_place_id=client_google_place_id, keywords=keywords)
            totals["processed_users"] += 1
            totals["observations_inserted"] += summary["observations_inserted"]
            totals["conquests_inserted"] += summary["conquests_inserted"]
            totals["suggestions_created"] += summary["suggestions_created"]
        return totals

    async def track_user(self, *, user_id: UUID, client_google_place_id: str, keywords: list[str]) -> dict[str, int]:
        if not (settings.google_maps_api_key or "").strip():
            return {
                "observations_inserted": 0,
                "conquests_inserted": 0,
                "suggestions_created": 0,
            }

        competitors = self.db.scalars(
            select(GrowthCompetitor)
            .where(GrowthCompetitor.user_id == user_id, GrowthCompetitor.is_active.is_(True))
            .order_by(GrowthCompetitor.created_at.asc())
            .limit(5)
        ).all()
        if not competitors:
            return {
                "observations_inserted": 0,
                "conquests_inserted": 0,
                "suggestions_created": 0,
            }

        client_place = await self._place_details(client_google_place_id)
        lat = client_place.get("lat")
        lng = client_place.get("lng")
        if lat is None or lng is None:
            return {
                "observations_inserted": 0,
                "conquests_inserted": 0,
                "suggestions_created": 0,
            }

        observed_at = datetime.now(timezone.utc).replace(microsecond=0)
        competitor_by_place_id = {row.google_place_id: row for row in competitors}
        observations_inserted = 0
        conquests_inserted = 0
        suggestions_created = 0

        for keyword in keywords[:5]:
            ranks = await self._search_keyword(keyword=keyword, lat=lat, lng=lng)
            if not ranks:
                continue

            client_rank = None
            rival_leader = None
            best_comp_rank = None
            for index, item in enumerate(ranks[:20], start=1):
                place_id = item.get("place_id")
                if place_id == client_google_place_id:
                    client_rank = index
                    observations_inserted += self._insert_observation(
                        user_id=user_id,
                        keyword=keyword,
                        location_label="default",
                        entity_type="client",
                        rank_position=index,
                        observed_at=observed_at,
                    )
                    continue
                competitor = competitor_by_place_id.get(place_id)
                if competitor is None:
                    continue
                observations_inserted += self._insert_observation(
                    user_id=user_id,
                    keyword=keyword,
                    location_label="default",
                    entity_type="competitor",
                    rank_position=index,
                    observed_at=observed_at,
                    competitor_id=competitor.id,
                )
                if best_comp_rank is None or index < best_comp_rank:
                    best_comp_rank = index
                if index == 1:
                    rival_leader = competitor

            previous_client_rank = self._previous_client_rank(user_id=user_id, keyword=keyword, before=observed_at)
            if client_rank is not None and previous_client_rank is not None and client_rank < previous_client_rank:
                displaced_competitor_id = rival_leader.id if rival_leader else None
                conquests_inserted += self._insert_conquest(
                    user_id=user_id,
                    keyword=keyword,
                    previous_rank=previous_client_rank,
                    new_rank=client_rank,
                    observed_at=observed_at,
                    displaced_competitor_id=displaced_competitor_id,
                )

            if rival_leader is not None and (client_rank is None or client_rank > 1):
                suggestions_created += self._create_rival_seo_refresh(
                    user_id=user_id,
                    competitor=rival_leader,
                    keyword=keyword,
                    observed_at=observed_at,
                    client_rank=client_rank,
                    rival_rank=1,
                )

        self.db.commit()
        return {
            "observations_inserted": observations_inserted,
            "conquests_inserted": conquests_inserted,
            "suggestions_created": suggestions_created,
        }

    def _normalize_keywords(self, csv_keywords: str | None) -> list[str]:
        values = [" ".join((item or "").split()).strip().lower() for item in (csv_keywords or "").split(",")]
        seen: set[str] = set()
        normalized: list[str] = []
        for value in values:
            if len(value) < 2 or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized[:5]

    async def _place_details(self, place_id: str) -> dict[str, Any]:
        params = {
            "place_id": place_id,
            "fields": "geometry,name",
            "language": "es",
            "key": settings.google_maps_api_key,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(_PLACES_DETAILS, params=params)
            response.raise_for_status()
            payload = response.json().get("result") or {}
        location = (payload.get("geometry") or {}).get("location") or {}
        return {
            "name": payload.get("name") or "",
            "lat": location.get("lat"),
            "lng": location.get("lng"),
        }

    async def _search_keyword(self, *, keyword: str, lat: float, lng: float) -> list[dict[str, Any]]:
        params = {
            "location": f"{lat},{lng}",
            "radius": 3500,
            "keyword": keyword,
            "language": "es",
            "key": settings.google_maps_api_key,
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(_PLACES_NEARBY, params=params)
            response.raise_for_status()
            return list(response.json().get("results") or [])

    def _insert_observation(
        self,
        *,
        user_id: UUID,
        keyword: str,
        location_label: str,
        entity_type: str,
        rank_position: int,
        observed_at: datetime,
        competitor_id: UUID | None = None,
    ) -> int:
        exists = self.db.scalars(
            select(GrowthSerpObservation.id).where(
                GrowthSerpObservation.user_id == user_id,
                GrowthSerpObservation.keyword == keyword,
                GrowthSerpObservation.location_label == location_label,
                GrowthSerpObservation.entity_type == entity_type,
                GrowthSerpObservation.competitor_id == competitor_id,
                GrowthSerpObservation.observed_at == observed_at,
            )
        ).first()
        if exists:
            return 0
        self.db.add(
            GrowthSerpObservation(
                user_id=user_id,
                competitor_id=competitor_id,
                keyword=keyword,
                location_label=location_label,
                entity_type=entity_type,
                rank_position=rank_position,
                observed_at=observed_at,
            )
        )
        return 1

    def _previous_client_rank(self, *, user_id: UUID, keyword: str, before: datetime) -> int | None:
        row = self.db.scalars(
            select(GrowthSerpObservation)
            .where(
                GrowthSerpObservation.user_id == user_id,
                GrowthSerpObservation.keyword == keyword,
                GrowthSerpObservation.entity_type == "client",
                GrowthSerpObservation.observed_at < before,
            )
            .order_by(desc(GrowthSerpObservation.observed_at))
            .limit(1)
        ).first()
        return row.rank_position if row else None

    def _insert_conquest(
        self,
        *,
        user_id: UUID,
        keyword: str,
        previous_rank: int,
        new_rank: int,
        observed_at: datetime,
        displaced_competitor_id: UUID | None,
    ) -> int:
        exists = self.db.scalars(
            select(GrowthKeywordConquestEvent.id).where(
                GrowthKeywordConquestEvent.user_id == user_id,
                GrowthKeywordConquestEvent.keyword == keyword,
                GrowthKeywordConquestEvent.conquered_at == observed_at,
            )
        ).first()
        if exists:
            return 0
        self.db.add(
            GrowthKeywordConquestEvent(
                user_id=user_id,
                keyword=keyword,
                location_label="default",
                displaced_competitor_id=displaced_competitor_id,
                previous_rank=previous_rank,
                new_rank=new_rank,
                conquered_at=observed_at,
            )
        )
        return 1

    def _create_rival_seo_refresh(
        self,
        *,
        user_id: UUID,
        competitor: GrowthCompetitor,
        keyword: str,
        observed_at: datetime,
        client_rank: int | None,
        rival_rank: int,
    ) -> int:
        latest_period = self.db.execute(
            select(GrowthCompetitorKeywordMetric.period_start, GrowthCompetitorKeywordMetric.period_end)
            .where(GrowthCompetitorKeywordMetric.competitor_id == competitor.id)
            .order_by(desc(GrowthCompetitorKeywordMetric.period_end))
            .limit(1)
        ).first()
        if not latest_period:
            return 0

        period_start, period_end = latest_period
        top_terms = self.db.scalars(
            select(GrowthCompetitorKeywordMetric)
            .where(
                GrowthCompetitorKeywordMetric.competitor_id == competitor.id,
                GrowthCompetitorKeywordMetric.period_start == period_start,
                GrowthCompetitorKeywordMetric.period_end == period_end,
            )
            .order_by(desc(GrowthCompetitorKeywordMetric.mentions_count))
            .limit(5)
        ).all()
        if not top_terms:
            return 0

        service = GrowthSeoService(self.db)
        suggestions = service.list_or_generate_suggestions(user_id=user_id)
        has_rival_suggestion = any(
            suggestion.status == "active"
            and suggestion.keyword == keyword
            and (suggestion.justification_payload or {}).get("source") == "rival_keyword_conquest"
            for suggestion in suggestions
        )
        if has_rival_suggestion:
            return 0

        connection = self.db.scalar(select(StarterProfileSettings).where(StarterProfileSettings.user_id == user_id))
        # Force-refresh is heavy; create one high-signal alert + suggestion directly from rival intel.
        current_description = ""
        from app.models import GoogleConnection, GrowthSeoAlert, GrowthSeoSuggestion

        google_connection = self.db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
        if google_connection and google_connection.google_profile_description:
            current_description = google_connection.google_profile_description

        top_keywords = [row.keyword for row in top_terms if row.keyword]
        headline_keyword = top_keywords[0]
        suggested_text = service._build_suggested_text(
            current_description=current_description,
            keyword=headline_keyword,
            suggestion_type="description_update",
        )
        suggestion = GrowthSeoSuggestion(
            user_id=user_id,
            suggestion_type="description_update",
            keyword=keyword,
            current_text=current_description,
            suggested_text=suggested_text,
            keywords_payload={"primary": headline_keyword, "related": top_keywords[1:4]},
            justification_payload={
                "source": "rival_keyword_conquest",
                "competitor_name": competitor.name,
                "competitor_id": str(competitor.id),
                "top_keywords": top_keywords,
                "client_rank": client_rank,
                "rival_rank": rival_rank,
                "observed_at": observed_at.isoformat(),
            },
            risk_level="medio",
            priority_score=92,
            source_period_start=period_start,
            source_period_end=period_end,
            status="active",
        )
        self.db.add(suggestion)
        self.db.flush()
        self.db.add(
            GrowthSeoAlert(
                user_id=user_id,
                suggestion_id=suggestion.id,
                title="Rival en posicion #1 detectado",
                message=(
                    f"{competitor.name} tomo la posicion #1 para '{keyword}'. "
                    f"Integra terminos como {', '.join(top_keywords[:3])} en tu perfil para contraatacar."
                ),
                severity="high",
                is_seen=False,
            )
        )
        try:
            GrowthEventNotificationService(self.db).publish_event(
                user_id=user_id,
                event_type="threat_detected",
                severity="high",
                title="Rival liderando keyword objetivo",
                message=f"{competitor.name} lidera '{keyword}' y Lokigi ya preparo una sugerencia SEO.",
                context_payload={"keyword": keyword, "competitor_name": competitor.name},
            )
        except Exception:
            pass
        return 1