"""
Onboarding flow for Starter Plan ($39/mes).

Steps:
  1. Google OAuth login  → handled by existing /oauth/google routes
  2. Business search     → GET /onboarding/step2  (SSR + HTMX fragments)
  3. Brand Voice Test    → GET /onboarding/step3  (SSR, 3-tone picker)
  4. Activation          → POST /onboarding/activate

HTMX fragments:
  GET  /onboarding/search          → autocomplete suggestion list
  GET  /onboarding/place-preview   → static map + business card
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import GoogleConnection, Review, StarterProfileSettings, User
from ..review_reply_engine import generate_reply_by_tone

log = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
templates = Jinja2Templates(directory="app/templates")

# ── helpers ───────────────────────────────────────────────────────────────────

_PLACES_AUTOCOMPLETE = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
_PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"
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


def _api_key_configured() -> bool:
    return bool((settings.google_maps_api_key or "").strip())


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
async def onboarding_step3(
    request: Request,
    user_id: UUID = Query(...),
    place_id: str = Query(...),
    business_name: str = Query(""),
    db: Session = Depends(get_db),
):
    """Step 3: Brand voice test with real review + 3-tone picker."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

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
            "step": 3,
            "review_text": review_text,
            "review_author": review_author,
            "review_stars": review_stars,
            "tone_options": tone_options,
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
    user_id: UUID = Query(...),
    place_id: str = Query(...),
    tone: str = Query("cercano"),
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

    db.commit()

    # HTMX redirect → send HX-Redirect header
    from fastapi.responses import Response
    redirect_url = f"/dashboard?user_id={user_id}"
    resp = Response(status_code=200, content="")
    resp.headers["HX-Redirect"] = redirect_url
    return resp
