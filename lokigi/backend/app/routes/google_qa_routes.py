"""Google Q&A Manager routes.

Endpoints:
  GET  /google/qa/manager                    SSR dashboard page
  GET  /api/google/qa/questions              List questions (JSON)
  GET  /api/google/qa/context                List business context entries
  POST /api/google/qa/context                Add / update a context entry
  DELETE /api/google/qa/context/{entry_id}   Soft-delete a context entry
  POST /api/google/qa/poll                   Manual poll for new questions
  POST /api/google/qa/answer/{question_id}   Send a manual answer
  POST /api/google/qa/approve/{question_id}  Approve + post auto-answer
  POST /api/google/qa/ignore/{question_id}   Mark as ignored

  HTMX fragments:
  GET  /google/qa/fragments/questions        Questions list HTML fragment
  GET  /google/qa/fragments/context          Context list HTML fragment
"""
from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.google_qa_service import GoogleQAService, QA_CONFIDENCE_THRESHOLD
from app.models import BusinessContext, GoogleConnection, GoogleQAQuestion, User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["google-qa"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _question_card(q: GoogleQAQuestion) -> dict:
    confidence = float(q.answer_confidence) if q.answer_confidence is not None else None
    return {
        "id": str(q.id),
        "question_text": q.question_text,
        "author": q.author_display_name or "Cliente",
        "upvotes": q.upvote_count,
        "detected_at": q.detected_at.strftime("%d %b %Y %H:%M") if q.detected_at else "",
        "status": q.status,
        "auto_answer": q.auto_answer_text or "",
        "confidence": confidence,
        "needs_review": q.status == "needs_intervention",
        "is_answered": q.status in ("auto_answered", "user_answered"),
        "sent_answer": q.sent_answer_text or "",
    }


def _context_card(e: BusinessContext) -> dict:
    return {
        "id": str(e.id),
        "context_type": e.context_type,
        "faq_question": e.faq_question or "",
        "content": e.content,
        "created_at": e.created_at.strftime("%d %b %Y") if e.created_at else "",
    }


def _get_business_name(db: Session, user_id: UUID) -> str:
    conn = db.query(GoogleConnection).filter(GoogleConnection.user_id == user_id).first()
    return (conn.business_name or "Tu Negocio") if conn else "Tu Negocio"


# ── SSR Page ──────────────────────────────────────────────────────────────────

@router.get("/google/qa/manager", response_class=HTMLResponse)
def qa_manager_page(
    request: Request,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = GoogleQAService(db)
    questions = service.list_questions(user_id, limit=50)
    context_entries = service.list_context(user_id)
    business_name = _get_business_name(db, user_id)

    pending_count = sum(1 for q in questions if q.status in ("pending", "needs_intervention"))
    auto_count = sum(1 for q in questions if q.status == "auto_answered")

    return templates.TemplateResponse(
        request=request,
        name="google_qa_manager.html",
        context={
            "user_id": str(user_id),
            "business_name": business_name,
            "questions": [_question_card(q) for q in questions],
            "context_entries": [_context_card(e) for e in context_entries],
            "pending_count": pending_count,
            "auto_count": auto_count,
            "confidence_threshold": int(QA_CONFIDENCE_THRESHOLD),
        },
    )


# ── HTMX Fragments ────────────────────────────────────────────────────────────

@router.get("/google/qa/fragments/questions", response_class=HTMLResponse)
def qa_questions_fragment(
    user_id: UUID = Query(...),
    status_filter: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    service = GoogleQAService(db)
    questions = service.list_questions(user_id, status_filter=status_filter, limit=50)
    cards = [_question_card(q) for q in questions]

    rows_html = ""
    for c in cards:
        badge_cls, badge_label = _status_badge(c["status"])
        conf_html = (
            f'<span class="text-xs text-emerald-300">{c["confidence"]:.0f}%</span>'
            if c["confidence"] is not None
            else '<span class="text-xs text-slate-500">—</span>'
        )
        answer_preview = (c["auto_answer"] or c["sent_answer"])[:120] or "(sin respuesta)"
        intervention_btn = ""
        if c["status"] == "needs_intervention":
            safe_answer = (c["auto_answer"] or "").replace("`", "'").replace("\\", "\\\\")
            intervention_btn = f"""
              <button class="rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-amber-400"
                onclick="openAnswerModal('{c['id']}', `{safe_answer}`)">
                Responder
              </button>"""
        rows_html += f"""
        <div id="qa-row-{c['id']}" class="glass rounded-2xl p-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:gap-4">
          <div class="flex-1 min-w-0">
            <p class="font-medium text-white truncate">{c['question_text']}</p>
            <p class="mt-1 text-xs text-slate-400">por {c['author']} · {c['detected_at']} · 👍 {c['upvotes']}</p>
            <p class="mt-2 text-sm text-slate-300 line-clamp-2">{answer_preview}</p>
          </div>
          <div class="flex flex-col items-end gap-2 shrink-0">
            <span class="rounded-full px-2 py-0.5 text-xs font-semibold {badge_cls}">{badge_label}</span>
            {conf_html}
            {intervention_btn}
          </div>
        </div>"""

    if not rows_html:
        rows_html = '<p class="text-center text-slate-400 py-8">Sin preguntas en este estado.</p>'

    return HTMLResponse(content=f'<div id="qa-questions-list" class="flex flex-col gap-3">{rows_html}</div>')


@router.get("/google/qa/fragments/context", response_class=HTMLResponse)
def qa_context_fragment(
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    service = GoogleQAService(db)
    entries = service.list_context(user_id)
    cards = [_context_card(e) for e in entries]

    rows_html = ""
    for c in cards:
        type_label = {"menu": "Menú/Servicios", "description": "Descripción", "faq": "FAQ"}.get(c["context_type"], c["context_type"])
        type_cls = {"menu": "bg-violet-500/20 text-violet-300", "description": "bg-sky-500/20 text-sky-300", "faq": "bg-emerald-500/20 text-emerald-300"}.get(c["context_type"], "bg-white/10 text-slate-300")
        faq_q_html = f'<p class="text-xs font-semibold text-emerald-300 mb-1">Q: {c["faq_question"]}</p>' if c["faq_question"] else ""
        rows_html += f"""
        <div id="ctx-row-{c['id']}" class="glass rounded-2xl p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <span class="inline-block rounded-full px-2 py-0.5 text-xs font-semibold {type_cls} mb-2">{type_label}</span>
              {faq_q_html}
              <p class="text-sm text-slate-200 line-clamp-3">{c['content']}</p>
              <p class="mt-1 text-xs text-slate-500">{c['created_at']}</p>
            </div>
            <button class="text-slate-400 hover:text-red-400 text-xs shrink-0 mt-1"
                hx-delete="/api/google/qa/context/{c['id']}?user_id={user_id}"
              hx-target="#ctx-row-{c['id']}"
              hx-swap="outerHTML"
              hx-confirm="¿Eliminar esta entrada del contexto?">
              ✕
            </button>
          </div>
        </div>"""

    if not rows_html:
        rows_html = '<p class="text-center text-slate-400 py-8">No hay contexto cargado aún.</p>'

    return HTMLResponse(content=f'<div id="qa-context-list" class="flex flex-col gap-3">{rows_html}</div>')


def _status_badge(status: str) -> tuple[str, str]:
    mapping = {
        "pending": ("bg-slate-500/30 text-slate-300", "Pendiente"),
        "auto_answered": ("bg-emerald-500/30 text-emerald-300", "Auto-respondida"),
        "needs_intervention": ("bg-amber-500/30 text-amber-300", "Requiere Intervención"),
        "user_answered": ("bg-sky-500/30 text-sky-300", "Respondida"),
        "ignored": ("bg-slate-600/30 text-slate-400", "Ignorada"),
    }
    return mapping.get(status, ("bg-white/10 text-slate-300", status))


# ── JSON API ──────────────────────────────────────────────────────────────────

@router.get("/api/google/qa/questions")
def api_list_questions(
    user_id: UUID = Query(...),
    status_filter: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    service = GoogleQAService(db)
    questions = service.list_questions(user_id, status_filter=status_filter, limit=limit)
    return {"items": [_question_card(q) for q in questions]}


@router.get("/api/google/qa/context")
def api_list_context(
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    service = GoogleQAService(db)
    entries = service.list_context(user_id)
    return {"items": [_context_card(e) for e in entries]}


class ContextCreateRequest(BaseModel):
    user_id: UUID
    location_id: str = Field(default="", max_length=128)
    context_type: str = Field(..., pattern="^(menu|description|faq)$")
    content: str = Field(..., min_length=1, max_length=4000)
    faq_question: str | None = Field(default=None, max_length=500)
    entry_id: UUID | None = None


@router.post("/api/google/qa/context", status_code=status.HTTP_201_CREATED)
def api_upsert_context(req: ContextCreateRequest, db: Session = Depends(get_db)):
    user = db.get(User, req.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Resolve location_id from connection if not provided
    location_id = req.location_id
    if not location_id:
        conn = db.query(GoogleConnection).filter(GoogleConnection.user_id == req.user_id).first()
        location_id = conn.location_id if conn else ""

    if req.context_type == "faq" and not req.faq_question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="faq_question is required for context_type='faq'",
        )

    service = GoogleQAService(db)
    try:
        entry = service.upsert_context(
            user_id=req.user_id,
            location_id=location_id,
            context_type=req.context_type,
            content=req.content,
            faq_question=req.faq_question,
            entry_id=req.entry_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _context_card(entry)


@router.delete("/api/google/qa/context/{entry_id}", status_code=status.HTTP_200_OK)
def api_delete_context(
    entry_id: UUID,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    service = GoogleQAService(db)
    try:
        service.delete_context(user_id=user_id, entry_id=entry_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"deleted": str(entry_id)}


@router.post("/api/google/qa/poll")
async def api_poll_questions(
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    service = GoogleQAService(db)
    try:
        stats = await service.poll_and_process(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return stats


class ManualAnswerRequest(BaseModel):
    user_id: UUID
    answer_text: str = Field(..., min_length=1, max_length=2000)


@router.post("/api/google/qa/answer/{question_id}")
async def api_send_manual_answer(
    question_id: UUID,
    req: ManualAnswerRequest,
    db: Session = Depends(get_db),
):
    service = GoogleQAService(db)
    try:
        question = await service.send_answer(
            user_id=req.user_id,
            question_id=question_id,
            answer_text=req.answer_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _question_card(question)


class ApproveAutoAnswerRequest(BaseModel):
    user_id: UUID
    edited_text: str | None = Field(default=None, max_length=2000)


@router.post("/api/google/qa/approve/{question_id}")
async def api_approve_auto_answer(
    question_id: UUID,
    req: ApproveAutoAnswerRequest,
    db: Session = Depends(get_db),
):
    service = GoogleQAService(db)
    try:
        question = await service.approve_and_send_auto_answer(
            user_id=req.user_id,
            question_id=question_id,
            edited_text=req.edited_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _question_card(question)


@router.post("/api/google/qa/ignore/{question_id}")
def api_ignore_question(
    question_id: UUID,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    service = GoogleQAService(db)
    try:
        question = service.ignore_question(user_id=user_id, question_id=question_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _question_card(question)
