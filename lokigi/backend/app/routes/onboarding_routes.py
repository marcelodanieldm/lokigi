"""
Onboarding flow for Starter Plan ($39/mes).

Steps:
    1. Google OAuth login     → handled by existing /oauth/google routes
    2. Business search        → GET /onboarding/step2
    3. Keyword radar setup    → GET /onboarding/step3
    4. Competitor selection   → GET /onboarding/step4
    5. Brand voice test       → GET /onboarding/step5
    6. Activation             → POST /onboarding/activate

HTMX fragments:
  GET  /onboarding/search          → autocomplete suggestion list
  GET  /onboarding/place-preview   → static map + business card
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus
from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import (
    GoogleConnection,
    GrowthBenchmarkComparison,
    GrowthClientSnapshot,
    GrowthCompetitor,
    GrowthCompetitorSnapshot,
    Review,
    StarterProfileSettings,
    User,
)
from ..review_reply_engine import generate_reply_by_tone

log = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
templates = Jinja2Templates(directory="app/templates")

# ── helpers ───────────────────────────────────────────────────────────────────

_PLACES_AUTOCOMPLETE = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
_PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"
_PLACES_NEARBY = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
_STATIC_MAP_BASE = "https://maps.googleapis.com/maps/api/staticmap"

_TONE_LABELS: dict[str, dict[str, str]] = {
    "cercano": {
        "label": "Amistoso",
        "icon": "😊",
        "description": "Cálido y cercano. Ideal para negocios de atención al cliente.",
        "color": "emerald",
    },
    "formal": {
        "label": "Profesional",
        "icon": "🎩",
        "description": "Formal y preciso. Ideal para consultorios, estudios y servicios.",
        "color": "blue",
    },
    "moderno": {
        "label": "Moderno",
        "icon": "⚡",
        "description": "Breve y directo. Ideal para marcas urbanas y tech.",
        "color": "violet",
    },
}

_KEYWORD_SUGGESTIONS: list[str] = [
    "Pizza artesanal",
    "Cerveceria pet friendly",
    "Hamburguesas gourmet",
    "Brunch de especialidad",
    "Cafe de origen",
    "Tacos mexicanos",
    "Comida vegana",
    "Cocteles de autor",
    "Desayuno saludable",
]

_DEMO_COMPETITORS: list[dict[str, Any]] = [
    {"place_id": "demo_comp_01", "name": "Pizza Bar Central", "address": "Centro", "rating": 4.8, "total_reviews": 632, "lat_offset": 0.004, "lng_offset": -0.003},
    {"place_id": "demo_comp_02", "name": "La Forneria Urbana", "address": "Casco historico", "rating": 4.7, "total_reviews": 588, "lat_offset": 0.006, "lng_offset": 0.002},
    {"place_id": "demo_comp_03", "name": "Brew House Local", "address": "Barrio Norte", "rating": 4.7, "total_reviews": 541, "lat_offset": -0.005, "lng_offset": 0.004},
    {"place_id": "demo_comp_04", "name": "Mercado Gourmet 24", "address": "Distrito gastronomico", "rating": 4.6, "total_reviews": 489, "lat_offset": -0.007, "lng_offset": -0.002},
    {"place_id": "demo_comp_05", "name": "Patio Artesano", "address": "Zona universitaria", "rating": 4.6, "total_reviews": 474, "lat_offset": 0.003, "lng_offset": 0.007},
    {"place_id": "demo_comp_06", "name": "Bistro del Parque", "address": "Parque central", "rating": 4.5, "total_reviews": 430, "lat_offset": 0.008, "lng_offset": -0.001},
    {"place_id": "demo_comp_07", "name": "Rincon de Barrio", "address": "Sector este", "rating": 4.5, "total_reviews": 397, "lat_offset": -0.004, "lng_offset": -0.006},
    {"place_id": "demo_comp_08", "name": "Studio Brunch", "address": "Avenida principal", "rating": 4.4, "total_reviews": 366, "lat_offset": 0.001, "lng_offset": 0.009},
    {"place_id": "demo_comp_09", "name": "Esquina Social", "address": "Zona peatonal", "rating": 4.4, "total_reviews": 342, "lat_offset": -0.008, "lng_offset": 0.001},
    {"place_id": "demo_comp_10", "name": "Fabrica de Sabores", "address": "Sector sur", "rating": 4.3, "total_reviews": 301, "lat_offset": 0.002, "lng_offset": -0.008},
]


def _api_key_configured() -> bool:
    return bool((settings.google_maps_api_key or "").strip())


def _normalize_focus_keywords(raw_keywords: list[str] | None = None, csv_keywords: str = "") -> list[str]:
    values = list(raw_keywords or [])
    if csv_keywords:
        values.extend(csv_keywords.split(","))

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        keyword = " ".join((value or "").strip().split())
        if len(keyword) < 2:
            continue
        lowered = keyword.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(keyword)
        if len(normalized) == 3:
            break
    return normalized


def _growth_sync_status(user_id: UUID, db: Session) -> dict[str, Any]:
    active_competitor_ids = db.scalars(
        select(GrowthCompetitor.id).where(
            GrowthCompetitor.user_id == user_id,
            GrowthCompetitor.is_active.is_(True),
        )
    ).all()
    active_count = len(active_competitor_ids)

    if active_count == 0:
        return {
            "ready": False,
            "status": "waiting-selection",
            "active_count": 0,
            "snapshot_count": 0,
            "benchmark_count": 0,
            "client_ready": False,
            "progress_pct": 5,
            "message": "Todavia no hay rivales activos para lanzar el primer Radar Competitivo.",
        }

    snapshot_count = db.scalar(
        select(func.count(func.distinct(GrowthCompetitorSnapshot.competitor_id))).where(
            GrowthCompetitorSnapshot.competitor_id.in_(active_competitor_ids)
        )
    ) or 0
    benchmark_count = db.scalar(
        select(func.count(func.distinct(GrowthBenchmarkComparison.competitor_id))).where(
            GrowthBenchmarkComparison.user_id == user_id,
            GrowthBenchmarkComparison.competitor_id.in_(active_competitor_ids),
        )
    ) or 0
    client_ready = bool(
        db.scalar(
            select(func.count(GrowthClientSnapshot.id)).where(GrowthClientSnapshot.user_id == user_id)
        )
        or 0
    )

    completed_units = snapshot_count + benchmark_count + (1 if client_ready else 0)
    total_units = (active_count * 2) + 1
    ready = snapshot_count >= active_count and benchmark_count >= active_count and client_ready
    progress_pct = max(10, min(100, round((completed_units / max(total_units, 1)) * 100)))
    message = (
        "El primer Radar Competitivo ya esta listo para entrar al Dashboard Hub."
        if ready
        else "ScraperWorker esta extrayendo reseñas, posts, servicios y comparativas iniciales de tus 5 rivales."
    )
    return {
        "ready": ready,
        "status": "ready" if ready else "syncing",
        "active_count": active_count,
        "snapshot_count": snapshot_count,
        "benchmark_count": benchmark_count,
        "client_ready": client_ready,
        "progress_pct": progress_pct,
        "message": message,
    }


def _build_competitor_map_url(center_lat: float | None, center_lng: float | None, competitors: list[dict[str, Any]]) -> str | None:
    if center_lat is None or center_lng is None or not _api_key_configured():
        return None

    marker_params = [f"markers=color:blue%7Clabel:C%7C{center_lat},{center_lng}"]
    for index, item in enumerate(competitors[:10], start=1):
        lat = item.get("lat")
        lng = item.get("lng")
        if lat is None or lng is None:
            continue
        label = str(index if index < 10 else 0)
        marker_params.append(f"markers=color:red%7Clabel:{label}%7C{lat},{lng}")

    return (
        f"{_STATIC_MAP_BASE}?size=960x420&maptype=roadmap&"
        + "&".join(marker_params)
        + f"&key={settings.google_maps_api_key}"
    )


def _score_competitor(item: dict[str, Any]) -> tuple[float, int, int]:
    search_hits = int(item.get("search_hits") or 0)
    rating = float(item.get("rating") or 0.0)
    reviews = int(item.get("total_reviews") or 0)
    return (search_hits, rating, reviews)


async def _discover_initial_competitors(
    *,
    place_id: str,
    business_name: str,
    keywords: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]], str | None]:
    client_place = await _place_details(place_id)
    lat = client_place.get("lat")
    lng = client_place.get("lng")

    if not _api_key_configured() or lat is None or lng is None:
        fallback_lat = float(lat or 40.4168)
        fallback_lng = float(lng or -3.7038)
        demo_rows: list[dict[str, Any]] = []
        for row in _DEMO_COMPETITORS:
            demo_rows.append(
                {
                    "place_id": row["place_id"],
                    "name": row["name"],
                    "address": row["address"],
                    "rating": row["rating"],
                    "total_reviews": row["total_reviews"],
                    "lat": fallback_lat + row["lat_offset"],
                    "lng": fallback_lng + row["lng_offset"],
                    "search_hits": 1,
                }
            )
        demo_rows.sort(key=_score_competitor, reverse=True)
        for index, row in enumerate(demo_rows, start=1):
            row["rank"] = index
        return client_place, demo_rows[:10], _build_competitor_map_url(fallback_lat, fallback_lng, demo_rows[:10])

    search_terms = keywords[:3] or [business_name]
    collected: dict[str, dict[str, Any]] = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for keyword in search_terms:
            params = {
                "location": f"{lat},{lng}",
                "radius": 2500,
                "keyword": keyword,
                "language": "es",
                "key": settings.google_maps_api_key,
            }
            response = await client.get(_PLACES_NEARBY, params=params)
            if response.status_code != 200:
                log.warning("Nearby search HTTP %s for keyword %s", response.status_code, keyword)
                continue
            for result in response.json().get("results", [])[:20]:
                candidate_place_id = result.get("place_id")
                if not candidate_place_id or candidate_place_id == place_id:
                    continue
                entry = collected.setdefault(
                    candidate_place_id,
                    {
                        "place_id": candidate_place_id,
                        "name": result.get("name") or "Competidor local",
                        "address": result.get("vicinity") or result.get("formatted_address") or "Ubicacion cercana",
                        "rating": result.get("rating") or 0.0,
                        "total_reviews": result.get("user_ratings_total") or 0,
                        "lat": (result.get("geometry") or {}).get("location", {}).get("lat"),
                        "lng": (result.get("geometry") or {}).get("location", {}).get("lng"),
                        "search_hits": 0,
                    },
                )
                entry["search_hits"] = int(entry.get("search_hits") or 0) + 1
                entry["rating"] = max(float(entry.get("rating") or 0.0), float(result.get("rating") or 0.0))
                entry["total_reviews"] = max(int(entry.get("total_reviews") or 0), int(result.get("user_ratings_total") or 0))

    ranked = sorted(collected.values(), key=_score_competitor, reverse=True)[:10]
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    return client_place, ranked, _build_competitor_map_url(lat, lng, ranked)


async def _places_autocomplete(query: str) -> list[dict[str, str]]:
    """Return up to 5 place suggestions from Google Places Autocomplete."""
    if not _api_key_configured():
        return []
    params = {
        "input": query,
        "types": "establishment",
        "language": "es",
        "key": settings.google_maps_api_key,
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(_PLACES_AUTOCOMPLETE, params=params)
    if resp.status_code != 200:
        log.warning("Places autocomplete HTTP %s", resp.status_code)
        return []
    data = resp.json()
    results = []
    for pred in data.get("predictions", [])[:5]:
        results.append(
            {
                "place_id": pred["place_id"],
                "main_text": pred["structured_formatting"].get("main_text", pred["description"]),
                "secondary_text": pred["structured_formatting"].get("secondary_text", ""),
                "description": pred["description"],
            }
        )
    return results


async def _place_details(place_id: str) -> dict[str, Any]:
    """Return name, address, rating, photo and lat/lng for a place_id."""
    if not _api_key_configured():
        return {}
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,rating,user_ratings_total,geometry,photos",
        "language": "es",
        "key": settings.google_maps_api_key,
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(_PLACES_DETAILS, params=params)
    if resp.status_code != 200:
        log.warning("Places details HTTP %s", resp.status_code)
        return {}
    result = resp.json().get("result", {})
    lat = result.get("geometry", {}).get("location", {}).get("lat")
    lng = result.get("geometry", {}).get("location", {}).get("lng")
    photo_ref = None
    photos = result.get("photos", [])
    if photos:
        photo_ref = photos[0].get("photo_reference")
    static_map_url = None
    if lat and lng:
        static_map_url = (
            f"{_STATIC_MAP_BASE}?center={lat},{lng}&zoom=16&size=480x200"
            f"&markers=color:red%7C{lat},{lng}&key={settings.google_maps_api_key}"
        )
    photo_url = None
    if photo_ref:
        photo_url = (
            f"https://maps.googleapis.com/maps/api/place/photo"
            f"?maxwidth=400&photoreference={photo_ref}&key={settings.google_maps_api_key}"
        )
    return {
        "place_id": place_id,
        "name": result.get("name", ""),
        "address": result.get("formatted_address", ""),
        "rating": result.get("rating"),
        "total_reviews": result.get("user_ratings_total"),
        "lat": lat,
        "lng": lng,
        "static_map_url": static_map_url,
        "photo_url": photo_url,
    }


def _pick_sample_review(db: Session, user_id: UUID) -> Review | None:
    """Pick one real past review to use in the brand-voice test."""
    conn = db.scalar(
        select(GoogleConnection).where(GoogleConnection.user_id == user_id)
    )
    if not conn:
        return None
    return db.scalar(
        select(Review)
        .where(Review.connection_id == conn.id)
        .where(Review.comment.isnot(None))
        .order_by(Review.create_time.desc())
        .limit(1)
    )


# ── SSR pages ─────────────────────────────────────────────────────────────────

@router.get("/step2", response_class=HTMLResponse)
async def onboarding_step2(
    request: Request,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    """Step 2: Business search + map confirmation."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    return templates.TemplateResponse(
        "onboarding_search.html",
        {
            "request": request,
            "user_id": str(user_id),
            "step": 2,
            "maps_configured": _api_key_configured(),
        },
    )


@router.get("/step3", response_class=HTMLResponse)
async def onboarding_step3_keywords(
    request: Request,
    user_id: UUID = Query(...),
    place_id: str = Query(...),
    business_name: str = Query(""),
    db: Session = Depends(get_db),
):
    """Step 3: pick the three main keywords for the Growth radar."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    profile_settings = db.scalar(select(StarterProfileSettings).where(StarterProfileSettings.user_id == user_id))
    existing_keywords = _normalize_focus_keywords(csv_keywords=profile_settings.focus_keywords if profile_settings else "")
    suggested_keywords = list(dict.fromkeys([*existing_keywords, *_KEYWORD_SUGGESTIONS]))[:8]

    return templates.TemplateResponse(
        "onboarding_keywords.html",
        {
            "request": request,
            "user_id": str(user_id),
            "place_id": place_id,
            "business_name": business_name or "Tu negocio",
            "step": 3,
            "existing_keywords": existing_keywords,
            "suggested_keywords": suggested_keywords,
        },
    )


@router.get("/step4", response_class=HTMLResponse)
async def onboarding_step4_competitors(
    request: Request,
    user_id: UUID = Query(...),
    place_id: str = Query(...),
    business_name: str = Query(""),
    keywords_csv: str = Query(""),
    db: Session = Depends(get_db),
):
    """Step 4: show initial top-10 rivals and let the user pick 5 direct competitors."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    focus_keywords = _normalize_focus_keywords(csv_keywords=keywords_csv)
    if len(focus_keywords) != 3:
        raise HTTPException(400, "Debes elegir exactamente 3 keywords principales")

    client_place, candidates, map_url = await _discover_initial_competitors(
        place_id=place_id,
        business_name=business_name or "Tu negocio",
        keywords=focus_keywords,
    )
    existing_active_ids = {
        row.google_place_id
        for row in db.scalars(
            select(GrowthCompetitor).where(
                GrowthCompetitor.user_id == user_id,
                GrowthCompetitor.is_active.is_(True),
            )
        ).all()
    }
    preselected_ids = [item["place_id"] for item in candidates if item["place_id"] in existing_active_ids][:5]
    if len(preselected_ids) < 5:
        for item in candidates:
            if item["place_id"] in preselected_ids:
                continue
            preselected_ids.append(item["place_id"])
            if len(preselected_ids) == 5:
                break

    return templates.TemplateResponse(
        "onboarding_competitors.html",
        {
            "request": request,
            "user_id": str(user_id),
            "place_id": place_id,
            "business_name": business_name or "Tu negocio",
            "step": 4,
            "focus_keywords": focus_keywords,
            "keywords_csv": ", ".join(focus_keywords),
            "client_place": client_place,
            "competitors": candidates,
            "map_url": map_url,
            "preselected_ids": preselected_ids,
        },
    )


@router.post("/step4/competitors")
async def onboarding_save_competitors(
    user_id: UUID = Form(...),
    place_id: str = Form(...),
    business_name: str = Form(""),
    keywords_csv: str = Form(""),
    selected_competitor_ids: list[str] = Form(default=[]),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    focus_keywords = _normalize_focus_keywords(csv_keywords=keywords_csv)
    if len(focus_keywords) != 3:
        raise HTTPException(400, "Debes elegir exactamente 3 keywords principales")

    normalized_ids = _normalize_focus_keywords(raw_keywords=selected_competitor_ids)
    if len(normalized_ids) != 5:
        raise HTTPException(400, "Debes elegir exactamente 5 competidores directos")

    _, candidates, _ = await _discover_initial_competitors(
        place_id=place_id,
        business_name=business_name or "Tu negocio",
        keywords=focus_keywords,
    )
    candidates_by_id = {item["place_id"]: item for item in candidates}
    missing_ids = [competitor_id for competitor_id in normalized_ids if competitor_id not in candidates_by_id]
    if missing_ids:
        raise HTTPException(400, "La seleccion de competidores ya no es valida. Recarga el ranking e intentalo de nuevo")

    existing_competitors = {
        row.google_place_id: row
        for row in db.scalars(
            select(GrowthCompetitor).where(GrowthCompetitor.user_id == user_id)
        ).all()
    }

    for competitor in existing_competitors.values():
        competitor.is_active = competitor.google_place_id in normalized_ids
        db.add(competitor)

    for competitor_place_id in normalized_ids:
        competitor_data = candidates_by_id.get(competitor_place_id)
        existing = existing_competitors.get(competitor_place_id)
        if existing:
            existing.name = competitor_data["name"]
            existing.city = competitor_data.get("address")
            existing.is_active = True
            db.add(existing)
            continue
        db.add(
            GrowthCompetitor(
                user_id=user_id,
                name=competitor_data["name"],
                google_place_id=competitor_place_id,
                city=competitor_data.get("address"),
                is_active=True,
            )
        )

    db.commit()
    redirect_url = (
        f"/onboarding/step5?user_id={user_id}&place_id={quote_plus(place_id)}"
        f"&business_name={quote_plus(business_name or 'Tu negocio')}"
        f"&keywords_csv={quote_plus(', '.join(focus_keywords))}"
    )
    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/step5", response_class=HTMLResponse)
async def onboarding_step5_brand_voice(
    request: Request,
    user_id: UUID = Query(...),
    place_id: str = Query(...),
    business_name: str = Query(""),
    keywords_csv: str = Query(""),
    db: Session = Depends(get_db),
):
    """Step 5: Brand voice test with real review + 3-tone picker."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    focus_keywords = _normalize_focus_keywords(csv_keywords=keywords_csv)
    if len(focus_keywords) != 3:
        raise HTTPException(400, "Debes elegir exactamente 3 keywords principales")

    sample_review = _pick_sample_review(db, user_id)

    # Fallback demo review if DB has none yet
    demo_text = (
        "El servicio fue muy bueno pero la espera fue un poco larga. "
        "El local está muy bien ubicado y el personal es amable."
    )
    review_text = (sample_review.comment if sample_review else demo_text) or demo_text
    review_author = (
        sample_review.author_display_name if sample_review else "Cliente anónimo"
    ) or "Cliente anónimo"
    review_stars = (sample_review.rating if sample_review else 4) or 4

    effective_name = business_name or "Tu Negocio"

    tone_options = []
    for tone_key, meta in _TONE_LABELS.items():
        reply = generate_reply_by_tone(
            tone=tone_key,
            review_text=review_text,
            stars=review_stars,
            business_name=effective_name,
            author_name=review_author,
        )
        tone_options.append(
            {
                "key": tone_key,
                "label": meta["label"],
                "icon": meta["icon"],
                "description": meta["description"],
                "color": meta["color"],
                "reply": reply,
            }
        )

    return templates.TemplateResponse(
        "onboarding_brand_voice.html",
        {
            "request": request,
            "user_id": str(user_id),
            "place_id": place_id,
            "business_name": effective_name,
            "step": 5,
            "review_text": review_text,
            "review_author": review_author,
            "review_stars": review_stars,
            "focus_keywords": focus_keywords,
            "competitor_count": db.scalar(
                select(func.count(GrowthCompetitor.id)).where(
                    GrowthCompetitor.user_id == user_id,
                    GrowthCompetitor.is_active.is_(True),
                )
            ) or 0,
            "keywords_csv": ", ".join(focus_keywords),
            "tone_options": tone_options,
        },
    )


@router.get("/sync", response_class=HTMLResponse)
async def onboarding_growth_sync(
    request: Request,
    user_id: UUID = Query(...),
    business_name: str = Query(""),
    task_id: str = Query(""),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    sync_status = _growth_sync_status(user_id, db)
    if sync_status["ready"]:
        return RedirectResponse(url=f"/growth/dashboard?user_id={user_id}", status_code=303)

    return templates.TemplateResponse(
        "onboarding_sync.html",
        {
            "request": request,
            "user_id": str(user_id),
            "business_name": business_name or "Tu negocio",
            "task_id": task_id,
            "sync": sync_status,
        },
    )


# ── HTMX fragment endpoints ───────────────────────────────────────────────────

@router.get("/search", response_class=HTMLResponse)
async def onboarding_search_fragment(
    request: Request,
    q: str = Query("", min_length=0),
):
    """HTMX: autocomplete suggestions list fragment."""
    suggestions: list[dict[str, str]] = []
    if len(q.strip()) >= 3:
        try:
            suggestions = await _places_autocomplete(q.strip())
        except Exception as exc:
            log.warning("Places autocomplete error: %s", exc)

    return templates.TemplateResponse(
        "_onboarding_results.html",
        {
            "request": request,
            "suggestions": suggestions,
            "query": q,
            "api_configured": _api_key_configured(),
        },
    )


@router.get("/place-preview", response_class=HTMLResponse)
async def onboarding_place_preview(
    request: Request,
    place_id: str = Query(...),
    user_id: str = Query(""),
):
    """HTMX: static map + business card confirmation fragment."""
    place: dict[str, Any] = {}
    if place_id:
        try:
            place = await _place_details(place_id)
        except Exception as exc:
            log.warning("Places details error: %s", exc)

    return templates.TemplateResponse(
        "_onboarding_preview.html",
        {
            "request": request,
            "place": place,
            "user_id": user_id,
        },
    )


# ── Activation endpoint ───────────────────────────────────────────────────────

@router.post("/activate", response_class=HTMLResponse)
async def onboarding_activate(
    request: Request,
    user_id: UUID = Form(...),
    place_id: str = Form(...),
    business_name: str = Form(""),
    tone: str = Form("cercano"),
    keywords_csv: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Final onboarding activation:
    - Persists chosen tone into GoogleConnection.preferred_tone
    - Creates StarterProfileSettings row if absent
    - Returns HTMX redirect response to the Starter dashboard
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    # Validate tone value
    allowed_tones = {"cercano", "formal", "moderno"}
    safe_tone = tone.lower().strip() if tone.lower().strip() in allowed_tones else "cercano"

    # Update preferred tone on the GoogleConnection
    conn = db.scalar(
        select(GoogleConnection).where(GoogleConnection.user_id == user_id)
    )
    if conn:
        conn.preferred_tone = safe_tone

    # Upsert StarterProfileSettings
    sps = db.scalar(
        select(StarterProfileSettings).where(StarterProfileSettings.user_id == user_id)
    )
    if not sps:
        sps = StarterProfileSettings(user_id=user_id)
        db.add(sps)

    focus_keywords = _normalize_focus_keywords(csv_keywords=keywords_csv)
    if len(focus_keywords) != 3:
        raise HTTPException(400, "Selecciona exactamente 3 keywords antes de activar Lokigi")
    sps.focus_keywords = ", ".join(focus_keywords)
    sps.client_google_place_id = place_id.strip()

    db.commit()

    task_id = ""
    try:
        from tasks.growth import run_initial_radar_sync

        async_result = run_initial_radar_sync.delay(str(user_id), place_id)
        task_id = async_result.id
    except Exception:
        log.exception("No se pudo encolar la sincronizacion inicial Growth para user_id=%s", user_id)

    # HTMX redirect → send HX-Redirect header
    from fastapi.responses import Response
    effective_business_name = business_name.strip() or (conn.business_name.strip() if conn and conn.business_name else "Tu negocio")
    redirect_url = (
        f"/onboarding/sync?user_id={user_id}"
        f"&business_name={quote_plus(effective_business_name)}"
        f"&task_id={quote_plus(task_id)}"
    )
    resp = Response(status_code=200, content="")
    resp.headers["HX-Redirect"] = redirect_url
    return resp
