"""Subscription Engine routes — limits, proration, trial, billing portal."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BillingInvoice, GoogleConnection, SubscriptionProfile, User
from app.subscription_engine import (
    PLAN_CONFIG,
    activate_free_trial,
    apply_plan_change,
    calculate_proration,
    get_or_create_profile,
    get_trial_status,
    get_usage_status,
    list_local_invoices,
    get_invoice_or_404,
    create_local_invoice,
)
from app.billing_service import list_subscription_invoices

logger = logging.getLogger(__name__)

router = APIRouter(tags=["subscription"])
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class PlanChangeRequest(BaseModel):
    user_id: UUID
    to_plan: str = Field(pattern="^(starter|growth|enterprise)$")


class TrialActivateRequest(BaseModel):
    user_id: UUID


class GenerateInvoiceRequest(BaseModel):
    user_id: UUID
    plan: str = Field(pattern="^(starter|growth|enterprise)$")
    period_start: date
    period_end: date
    description: str | None = None
    proration_cents: int = 0


# ─── Self-service portal HTML ─────────────────────────────────────────────────

@router.get("/subscription/portal", response_class=HTMLResponse, include_in_schema=False)
async def subscription_portal(
    request: Request,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    usage = get_usage_status(db, user_id)
    trial = get_trial_status(db, user_id)
    local_invoices = list_local_invoices(db, user_id)

    # Fetch Stripe invoices and merge
    stripe_invoices = []
    try:
        stripe_invoices = list_subscription_invoices(db, user_id, limit=12)
    except Exception:
        pass  # Stripe not configured or down — degrade gracefully

    # Merge: Stripe invoices tagged with source="stripe", local tagged with source="lokigi"
    for inv in stripe_invoices:
        inv["source"] = "stripe"
    all_invoices = sorted(
        local_invoices + stripe_invoices,
        key=lambda x: x.get("created_at", "") or "",
        reverse=True,
    )

    # Pending proration credits
    from app.models import ProrationCredit
    from sqlalchemy import select as sa_select
    pending_prorations = list(
        db.scalars(
            sa_select(ProrationCredit)
            .where(ProrationCredit.user_id == user_id, ProrationCredit.status == "pending")
            .order_by(ProrationCredit.created_at.desc())
        ).all()
    )

    plan_options = [
        {
            "key": k,
            "label": v["label"],
            "price_usd": v["price_cents"] / 100,
            "locations": v["locations_hard"],
            "ai_credits": v["ai_credits_monthly"],
            "is_current": k == (usage["base_plan"]),
        }
        for k, v in PLAN_CONFIG.items()
    ]

    return templates.TemplateResponse(
        request,
        "subscription_portal.html",
        {
            "user_id": str(user_id),
            "usage": usage,
            "trial": trial,
            "invoices": all_invoices,
            "pending_prorations": [
                {
                    "id": str(p.id),
                    "from_plan": p.from_plan,
                    "to_plan": p.to_plan,
                    "net_cents": p.net_cents,
                    "change_date": p.change_date.isoformat(),
                }
                for p in pending_prorations
            ],
            "plan_options": plan_options,
        },
    )


# ─── Usage & status ───────────────────────────────────────────────────────────

@router.get("/api/v1/subscription/usage")
def api_usage(
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return get_usage_status(db, user_id)


# ─── Proration preview ────────────────────────────────────────────────────────

@router.get("/api/v1/subscription/proration/preview")
def api_proration_preview(
    user_id: UUID = Query(...),
    to_plan: str = Query(..., pattern="^(starter|growth|enterprise)$"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    profile = get_or_create_profile(db, user_id)
    from_plan = profile.subscription_plan or "starter"
    period_end = profile.current_period_end.date() if profile.current_period_end else None
    return calculate_proration(from_plan, to_plan, period_end=period_end)


# ─── Plan change (upgrade / downgrade) ───────────────────────────────────────

@router.post("/api/v1/subscription/change-plan")
def api_change_plan(
    body: PlanChangeRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = apply_plan_change(db, body.user_id, body.to_plan)
    db.commit()
    return result


# ─── Free trial ───────────────────────────────────────────────────────────────

@router.post("/api/v1/subscription/trial/activate")
def api_trial_activate(
    body: TrialActivateRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = activate_free_trial(db, body.user_id)
    db.commit()
    return result


@router.get("/api/v1/subscription/trial/status")
def api_trial_status(
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return get_trial_status(db, user_id)


# ─── Invoices ─────────────────────────────────────────────────────────────────

@router.get("/api/v1/subscription/invoices")
def api_invoices(
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    local = list_local_invoices(db, user_id)
    stripe_invs: list[dict[str, Any]] = []
    try:
        stripe_invs = list_subscription_invoices(db, user_id, limit=12)
        for inv in stripe_invs:
            inv["source"] = "stripe"
    except Exception:
        pass
    return sorted(local + stripe_invs, key=lambda x: x.get("created_at", "") or "", reverse=True)


@router.post("/api/v1/subscription/invoices/generate")
def api_generate_invoice(
    body: GenerateInvoiceRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a local BillingInvoice record and immediately render the PDF."""
    plan_cfg = PLAN_CONFIG.get(body.plan, PLAN_CONFIG["starter"])
    inv = create_local_invoice(
        db,
        user_id=body.user_id,
        plan=body.plan,
        period_start=body.period_start,
        period_end=body.period_end,
        amount_cents=plan_cfg["price_cents"] + body.proration_cents,
        description=body.description,
    )

    # Eagerly generate PDF and store path
    _generate_and_store_pdf(db, inv, proration_cents=body.proration_cents)
    db.commit()

    return {
        "invoice_id": str(inv.id),
        "invoice_number": inv.invoice_number,
        "pdf_url": f"/api/v1/subscription/invoices/{inv.id}/pdf",
    }


@router.get("/api/v1/subscription/invoices/{invoice_id}/pdf")
def api_invoice_pdf(
    invoice_id: UUID,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db),
) -> Response:
    """Stream a WeasyPrint PDF for a local invoice."""
    inv = get_invoice_or_404(db, user_id, invoice_id)

    # Lookup customer info
    user = db.scalar(select(User).where(User.id == user_id))
    customer_email = user.email if user else ""
    customer_name = customer_email.split("@")[0].title() if customer_email else "Cliente"

    from app.invoice_pdf_service import render_invoice_pdf
    pdf_bytes = render_invoice_pdf(
        invoice_number=inv.invoice_number,
        issued_date=inv.created_at.date(),
        period_start=inv.period_start,
        period_end=inv.period_end,
        plan=inv.plan,
        amount_cents=inv.amount_cents,
        currency=inv.currency,
        status=inv.status,
        customer_name=customer_name,
        customer_email=customer_email,
        description=inv.description,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{inv.invoice_number}.pdf"'},
    )


# ─── Internal helper ─────────────────────────────────────────────────────────

def _generate_and_store_pdf(
    db: Session,
    inv: BillingInvoice,
    proration_cents: int = 0,
) -> None:
    """Render PDF and update pdf_path on the invoice row (no commit)."""
    import os
    from app.invoice_pdf_service import render_invoice_pdf

    user = db.scalar(select(User).where(User.id == inv.user_id))
    customer_email = user.email if user else ""
    customer_name = customer_email.split("@")[0].title() if customer_email else "Cliente"

    pdf_bytes = render_invoice_pdf(
        invoice_number=inv.invoice_number,
        issued_date=inv.created_at.date(),
        period_start=inv.period_start,
        period_end=inv.period_end,
        plan=inv.plan,
        amount_cents=inv.amount_cents,
        currency=inv.currency,
        status=inv.status,
        customer_name=customer_name,
        customer_email=customer_email,
        description=inv.description,
        proration_cents=proration_cents,
    )

    from app.config import settings
    output_dir = Path(settings.assets_upload_dir) / "invoices"
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{inv.invoice_number}.pdf"
    pdf_path.write_bytes(pdf_bytes)
    inv.pdf_path = str(pdf_path)
