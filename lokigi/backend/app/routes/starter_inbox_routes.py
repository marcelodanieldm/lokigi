from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GoogleConnection, Review, User
from app.services import get_pending_approvals, regenerate_review_reply, send_review_reply


router = APIRouter(tags=["starter-inbox"])
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _format_time(value: datetime | None) -> str:
    if value is None:
        return "Ahora"
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _build_pending_cards(db: Session, user_id: UUID) -> list[dict]:
    reviews = get_pending_approvals(db, str(user_id))
    cards: list[dict] = []
    for review in reviews:
        if (review.rating or 0) >= 4:
            urgency = "baja"
        elif (review.rating or 0) == 3:
            urgency = "media"
        else:
            urgency = "alta"
        cards.append(
            {
                "id": str(review.id),
                "review_id": review.review_id,
                "author": review.author_display_name or "Cliente",
                "stars": review.rating or 0,
                "comment": review.comment or "(sin comentario)",
                "draft": (review.pending_response.draft_text if review.pending_response else review.reply_public_text) or "",
                "urgency": urgency,
                "detected_language": review.reply_detected_language or "es",
                "decided_at": _format_time(review.reply_decided_at),
            }
        )
    return cards


def _card_payload(review: Review) -> dict:
    return {
        "id": str(review.id),
        "review_id": review.review_id,
        "author": review.author_display_name or "Cliente",
        "stars": review.rating or 0,
        "comment": review.comment or "(sin comentario)",
        "draft": (review.pending_response.draft_text if review.pending_response else review.reply_public_text) or "",
        "urgency": "baja" if (review.rating or 0) >= 4 else ("media" if (review.rating or 0) == 3 else "alta"),
        "detected_language": review.reply_detected_language or "es",
        "decided_at": _format_time(review.reply_decided_at),
    }


@router.get("/starter/inbox", response_class=HTMLResponse)
def starter_inbox_page(
    request: Request,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    if not connection:
        raise HTTPException(status_code=404, detail="User not connected")

    return templates.TemplateResponse(
        request=request,
        name="starter_inbox.html",
        context={
            "request": request,
            "user_id": str(user_id),
            "business_name": connection.business_name or connection.google_account_name,
            "pending_cards": _build_pending_cards(db, user_id),
        },
    )


@router.get("/starter/inbox/fragments/list", response_class=HTMLResponse)
def starter_inbox_list_fragment(
    request: Request,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="starter_inbox_fragments.html",
        context={
            "request": request,
            "fragment": "list",
            "pending_cards": _build_pending_cards(db, user_id),
            "user_id": str(user_id),
        },
    )


@router.post("/starter/inbox/{review_id}/approve", response_class=HTMLResponse)
@router.post("/reviews/{review_id}/approve", response_class=HTMLResponse)
async def starter_inbox_approve_fragment(
    request: Request,
    review_id: UUID,
    db: Session = Depends(get_db),
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    form = await request.form()
    reply_text = str(form.get("reply_text") or review.reply_public_text or "").strip()
    if not reply_text:
        raise HTTPException(status_code=400, detail="reply_text must not be empty")
    await send_review_reply(db=db, review=review, reply_text=reply_text)
    return HTMLResponse("", status_code=200)


@router.post("/starter/inbox/{review_id}/regenerate", response_class=HTMLResponse)
@router.post("/reviews/{review_id}/regenerate", response_class=HTMLResponse)
async def starter_inbox_regenerate_fragment(
    request: Request,
    review_id: UUID,
    db: Session = Depends(get_db),
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    updated = await regenerate_review_reply(db=db, review=review)
    user_id = str(updated.connection.user_id)
    return templates.TemplateResponse(
        request=request,
        name="starter_inbox_fragments.html",
        context={
            "request": request,
            "fragment": "card",
            "card": _card_payload(updated),
            "user_id": user_id,
        },
    )


@router.post("/starter/inbox/{review_id}/edit", response_class=HTMLResponse)
@router.post("/reviews/{review_id}/edit", response_class=HTMLResponse)
async def starter_inbox_edit_fragment(
    request: Request,
    review_id: UUID,
    db: Session = Depends(get_db),
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    form = await request.form()
    reply_text = str(form.get("reply_text") or "")
    cleaned = reply_text.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="reply_text must not be empty")
    review.reply_public_text = cleaned
    if review.pending_response:
        review.pending_response.draft_text = cleaned
        review.pending_response.status = "pending"
    db.commit()
    db.refresh(review)
    user_id = str(review.connection.user_id)
    return templates.TemplateResponse(
        request=request,
        name="starter_inbox_fragments.html",
        context={
            "request": request,
            "fragment": "card",
            "card": _card_payload(review),
            "user_id": user_id,
        },
    )


@router.get("/starter/auto-send", response_class=HTMLResponse)
def starter_auto_send_page(
    request: Request,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    if not connection:
        raise HTTPException(status_code=404, detail="User not connected")
    return templates.TemplateResponse(
        request=request,
        name="starter_auto_send.html",
        context={
            "request": request,
            "user_id": str(user_id),
            "business_name": connection.business_name or connection.google_account_name,
            "auto_send_positive": not connection.manual_approval_enabled,
        },
    )


@router.post("/starter/auto-send", response_class=HTMLResponse)
async def starter_auto_send_save(
    request: Request,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    if not connection:
        raise HTTPException(status_code=404, detail="User not connected")

    form = await request.form()
    auto_send_positive = str(form.get("respond_four_five_stars_automatically") or "").lower() in {"true", "1", "on"}
    connection.manual_approval_enabled = not auto_send_positive
    db.commit()
    return templates.TemplateResponse(
        request=request,
        name="starter_inbox_fragments.html",
        context={
            "request": request,
            "fragment": "toast",
            "kind": "success",
            "message": "Configuración de auto-envío actualizada.",
        },
    )