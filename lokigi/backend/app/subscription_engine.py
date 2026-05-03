"""Subscription Engine — hard/soft limits, pro-rated plan changes, free trials.

Terminology
-----------
- Hard limit  : action is BLOCKED (raises HTTP 402/403).
- Soft limit  : action is ALLOWED but a warning is returned to the caller.
- Proration   : mid-cycle plan change; credit/debit calculated proportionally.
- Free trial  : 7-day Growth feature set activation for Starter users.
"""

from __future__ import annotations

import calendar
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    BillingInvoice,
    GoogleConnection,
    ProrationCredit,
    SubscriptionProfile,
    User,
)

logger = logging.getLogger(__name__)

# ─── Plan configuration ────────────────────────────────────────────────────────
PLAN_CONFIG: dict[str, dict[str, Any]] = {
    "starter": {
        "label": "Starter",
        "price_cents": 3900,          # $39.00 / month
        "locations_hard": 1,          # max connected Google locations
        "ai_credits_monthly": 500,    # auto-replies / AI calls per month
        "ai_credits_soft_pct": 80,    # warn at 80 % of quota
    },
    "growth": {
        "label": "Growth",
        "price_cents": 8900,          # $89.00 / month
        "locations_hard": 10,
        "ai_credits_monthly": 5000,
        "ai_credits_soft_pct": 80,
    },
    "enterprise": {
        "label": "Enterprise",
        "price_cents": 29900,         # $299.00 / month
        "locations_hard": None,       # unlimited
        "ai_credits_monthly": None,   # unlimited
        "ai_credits_soft_pct": 90,
    },
}

FREE_TRIAL_DAYS = 7
BILLING_PERIOD_DAYS = 30  # approximate; used for proration when no Stripe period


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _today() -> date:
    return _now_utc().date()


def _effective_plan(profile: SubscriptionProfile) -> str:
    """Return the plan that should be enforced right now.
    During an active trial the trial plan takes precedence.
    """
    if (
        profile.trial_plan
        and profile.trial_ends_at
        and profile.trial_ends_at.replace(tzinfo=timezone.utc) > _now_utc()
    ):
        return profile.trial_plan
    return profile.subscription_plan or "starter"


# ─── 1. Hard / soft limit checks ─────────────────────────────────────────────

def get_or_create_profile(db: Session, user_id: UUID) -> SubscriptionProfile:
    profile = db.scalar(select(SubscriptionProfile).where(SubscriptionProfile.user_id == user_id))
    if not profile:
        profile = SubscriptionProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


def _reset_monthly_credits_if_needed(profile: SubscriptionProfile) -> None:
    """Reset ai_credits_used on the first call of a new calendar month (in-place, no flush)."""
    now = _now_utc()
    if profile.ai_credits_reset_at is None or profile.ai_credits_reset_at.month != now.month or profile.ai_credits_reset_at.year != now.year:
        profile.ai_credits_used = 0
        profile.ai_credits_reset_at = now


def check_location_hard_limit(db: Session, user_id: UUID) -> None:
    """Raise HTTP 402 if the user is about to exceed the location hard limit."""
    profile = get_or_create_profile(db, user_id)
    plan = _effective_plan(profile)
    cfg = PLAN_CONFIG.get(plan, PLAN_CONFIG["starter"])
    hard_cap = cfg["locations_hard"]
    if hard_cap is None:
        return  # unlimited

    current_count = db.scalar(
        select(func.count(GoogleConnection.id)).where(GoogleConnection.user_id == user_id)
    ) or 0

    if current_count >= hard_cap:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "LOCATION_LIMIT_REACHED",
                "plan": plan,
                "limit": hard_cap,
                "current": current_count,
                "message": (
                    f"El Plan {cfg['label']} permite máximo {hard_cap} "
                    f"ubicación{'es' if hard_cap != 1 else ''} conectada{'s' if hard_cap != 1 else ''}. "
                    "Actualiza tu plan para agregar más ubicaciones."
                ),
                "upgrade_cta": True,
            },
        )


def increment_ai_credit(db: Session, user_id: UUID) -> dict[str, Any]:
    """Consume one AI credit and return the current usage state.
    Raises HTTP 402 on hard limit; returns soft-limit warning in the dict.
    """
    profile = get_or_create_profile(db, user_id)
    _reset_monthly_credits_if_needed(profile)
    plan = _effective_plan(profile)
    cfg = PLAN_CONFIG.get(plan, PLAN_CONFIG["starter"])
    monthly_cap = cfg["ai_credits_monthly"]

    # Hard limit
    if monthly_cap is not None and profile.ai_credits_used >= monthly_cap:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "AI_CREDITS_EXHAUSTED",
                "plan": plan,
                "limit": monthly_cap,
                "used": profile.ai_credits_used,
                "message": (
                    f"Has agotado los {monthly_cap} créditos de IA del mes. "
                    "Actualiza tu plan para continuar usando respuestas automáticas."
                ),
                "upgrade_cta": True,
            },
        )

    profile.ai_credits_used += 1
    db.flush()

    soft_warning = None
    if monthly_cap is not None:
        used_pct = profile.ai_credits_used / monthly_cap * 100
        if used_pct >= cfg["ai_credits_soft_pct"]:
            soft_warning = {
                "code": "AI_CREDITS_SOFT_LIMIT",
                "message": (
                    f"Estás usando el {used_pct:.0f}% de tus créditos de IA del mes "
                    f"({profile.ai_credits_used}/{monthly_cap}). Considera actualizar tu plan."
                ),
                "used": profile.ai_credits_used,
                "limit": monthly_cap,
                "pct": round(used_pct, 1),
            }

    return {
        "credits_used": profile.ai_credits_used,
        "credits_limit": monthly_cap,
        "soft_warning": soft_warning,
    }


def get_usage_status(db: Session, user_id: UUID) -> dict[str, Any]:
    """Full usage snapshot for the subscription portal UI."""
    profile = get_or_create_profile(db, user_id)
    _reset_monthly_credits_if_needed(profile)
    db.flush()

    plan = _effective_plan(profile)
    base_plan = profile.subscription_plan or "starter"
    cfg = PLAN_CONFIG.get(plan, PLAN_CONFIG["starter"])
    base_cfg = PLAN_CONFIG.get(base_plan, PLAN_CONFIG["starter"])

    location_count = db.scalar(
        select(func.count(GoogleConnection.id)).where(GoogleConnection.user_id == user_id)
    ) or 0

    ai_used = profile.ai_credits_used
    ai_cap = cfg["ai_credits_monthly"]
    ai_pct = round(ai_used / ai_cap * 100, 1) if ai_cap else 0
    ai_soft_threshold = cfg["ai_credits_soft_pct"]

    loc_cap = cfg["locations_hard"]
    loc_pct = round(location_count / loc_cap * 100, 1) if loc_cap else 0

    # Trial status
    trial_active = (
        profile.trial_plan is not None
        and profile.trial_ends_at is not None
        and profile.trial_ends_at.replace(tzinfo=timezone.utc) > _now_utc()
    )
    trial_remaining_h = None
    if trial_active and profile.trial_ends_at:
        delta = profile.trial_ends_at.replace(tzinfo=timezone.utc) - _now_utc()
        trial_remaining_h = max(0, int(delta.total_seconds() / 3600))

    return {
        "base_plan": base_plan,
        "base_plan_label": base_cfg["label"],
        "effective_plan": plan,
        "effective_plan_label": cfg["label"],
        "status": profile.subscription_status or "active",
        "trial_active": trial_active,
        "trial_plan": profile.trial_plan,
        "trial_ends_at": profile.trial_ends_at.isoformat() if profile.trial_ends_at else None,
        "trial_remaining_hours": trial_remaining_h,
        "current_period_end": profile.current_period_end.isoformat() if profile.current_period_end else None,
        "pricing": {
            "monthly_cents": base_cfg["price_cents"],
            "monthly_usd": base_cfg["price_cents"] / 100,
        },
        "locations": {
            "used": location_count,
            "limit": loc_cap,
            "pct": loc_pct,
            "at_hard_limit": loc_cap is not None and location_count >= loc_cap,
        },
        "ai_credits": {
            "used": ai_used,
            "limit": ai_cap,
            "pct": ai_pct,
            "at_hard_limit": ai_cap is not None and ai_used >= ai_cap,
            "at_soft_limit": ai_cap is not None and ai_pct >= ai_soft_threshold,
            "soft_threshold_pct": ai_soft_threshold,
        },
        "can_activate_trial": (
            base_plan == "starter"
            and not trial_active
            and profile.trial_plan is None  # never trialed before
        ),
    }


# ─── 2. Pro-rated plan change ─────────────────────────────────────────────────

def calculate_proration(
    from_plan: str,
    to_plan: str,
    change_date: date | None = None,
    period_end: date | None = None,
) -> dict[str, Any]:
    """Calculate the proration credit/debit for a mid-cycle plan change.

    Returns a breakdown dict (does NOT write to DB).
    """
    change_date = change_date or _today()
    from_cfg = PLAN_CONFIG.get(from_plan.lower(), PLAN_CONFIG["starter"])
    to_cfg = PLAN_CONFIG.get(to_plan.lower(), PLAN_CONFIG["starter"])

    # Days remaining in period
    if period_end:
        days_remaining = max(0, (period_end - change_date).days)
        period_days = max(1, (period_end - (period_end.replace(day=1))).days + 1)
    else:
        # Approximate: assume billing period = calendar month
        _, days_in_month = calendar.monthrange(change_date.year, change_date.month)
        next_month = change_date.replace(day=1) + timedelta(days=days_in_month)
        days_remaining = max(0, (next_month - change_date).days)
        period_days = days_in_month

    daily_from = from_cfg["price_cents"] / period_days
    daily_to = to_cfg["price_cents"] / period_days

    credit_cents = round(daily_from * days_remaining)
    debit_cents = round(daily_to * days_remaining)
    net_cents = debit_cents - credit_cents  # positive = extra charge, negative = refund

    return {
        "from_plan": from_plan,
        "to_plan": to_plan,
        "change_date": change_date.isoformat(),
        "days_remaining": days_remaining,
        "period_days": period_days,
        "from_price_usd": from_cfg["price_cents"] / 100,
        "to_price_usd": to_cfg["price_cents"] / 100,
        "credit_usd": credit_cents / 100,
        "debit_usd": debit_cents / 100,
        "net_usd": net_cents / 100,
        "net_cents": net_cents,
        "summary": (
            f"Crédito de ${credit_cents/100:.2f} por {days_remaining} días restantes de {from_cfg['label']}. "
            f"Cargo de ${debit_cents/100:.2f} por {days_remaining} días de {to_cfg['label']}. "
            f"{'Cargo adicional' if net_cents > 0 else 'Crédito'} neto: ${abs(net_cents)/100:.2f}."
        ),
    }


def apply_plan_change(
    db: Session,
    user_id: UUID,
    to_plan: str,
) -> dict[str, Any]:
    """Change the user's plan and persist a ProrationCredit record.
    Does NOT call Stripe — that must be done separately in the route handler.
    """
    to_plan = to_plan.lower()
    if to_plan not in PLAN_CONFIG:
        raise HTTPException(status_code=400, detail=f"Plan '{to_plan}' not recognized.")

    profile = get_or_create_profile(db, user_id)
    from_plan = profile.subscription_plan or "starter"

    if from_plan == to_plan:
        raise HTTPException(status_code=400, detail="El usuario ya tiene ese plan.")

    proration = calculate_proration(
        from_plan,
        to_plan,
        period_end=profile.current_period_end.date() if profile.current_period_end else None,
    )

    credit = ProrationCredit(
        id=uuid.uuid4(),
        user_id=user_id,
        from_plan=from_plan,
        to_plan=to_plan,
        change_date=_today(),
        days_remaining=proration["days_remaining"],
        credit_cents=round(proration["credit_usd"] * 100),
        debit_cents=round(proration["debit_usd"] * 100),
        net_cents=proration["net_cents"],
        status="pending",
    )
    db.add(credit)

    profile.subscription_plan = to_plan
    db.flush()

    logger.info("Plan changed: user=%s %s→%s net_cents=%d", user_id, from_plan, to_plan, proration["net_cents"])
    return {
        "previous_plan": from_plan,
        "new_plan": to_plan,
        "proration": proration,
        "proration_id": str(credit.id),
    }


# ─── 3. Free trial ─────────────────────────────────────────────────────────────

def activate_free_trial(db: Session, user_id: UUID) -> dict[str, Any]:
    """Grant 7-day Growth trial to a Starter user.
    Idempotent: raises 409 if a trial has already been activated.
    """
    profile = get_or_create_profile(db, user_id)

    if profile.trial_plan is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "TRIAL_ALREADY_USED",
                "message": "Ya utilizaste tu prueba gratuita de Growth. Solo se permite un período de prueba por cuenta.",
            },
        )

    if (profile.subscription_plan or "starter") != "starter":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "TRIAL_NOT_AVAILABLE",
                "message": "La prueba gratuita de Growth solo está disponible para usuarios del Plan Starter.",
            },
        )

    ends_at = _now_utc() + timedelta(days=FREE_TRIAL_DAYS)
    profile.trial_plan = "growth"
    profile.trial_ends_at = ends_at
    db.flush()

    logger.info("Free trial activated: user=%s ends_at=%s", user_id, ends_at.isoformat())
    return {
        "trial_plan": "growth",
        "activated_at": _now_utc().isoformat(),
        "ends_at": ends_at.isoformat(),
        "days": FREE_TRIAL_DAYS,
        "message": (
            f"¡Prueba de Growth activada! Tienes {FREE_TRIAL_DAYS} días de acceso a todas las "
            "funcionalidades del Plan Growth. Al vencer, tu cuenta regresará al Plan Starter."
        ),
    }


def get_trial_status(db: Session, user_id: UUID) -> dict[str, Any]:
    """Return trial state (also auto-expires in the DB if the trial has passed)."""
    profile = get_or_create_profile(db, user_id)

    if profile.trial_plan is None:
        return {"has_trial": False, "trial_used": False, "trial_active": False}

    ends_at = profile.trial_ends_at
    if ends_at is None:
        return {"has_trial": True, "trial_used": True, "trial_active": False}

    now = _now_utc()
    is_active = ends_at.replace(tzinfo=timezone.utc) > now
    remaining_seconds = max(0, (ends_at.replace(tzinfo=timezone.utc) - now).total_seconds())

    return {
        "has_trial": True,
        "trial_used": True,
        "trial_active": is_active,
        "trial_plan": profile.trial_plan,
        "ends_at": ends_at.isoformat(),
        "remaining_hours": round(remaining_seconds / 3600, 1),
        "remaining_days": round(remaining_seconds / 86400, 1),
    }


# ─── 4. Billing invoices ───────────────────────────────────────────────────────

def list_local_invoices(db: Session, user_id: UUID, limit: int = 24) -> list[dict[str, Any]]:
    rows = list(
        db.scalars(
            select(BillingInvoice)
            .where(BillingInvoice.user_id == user_id)
            .order_by(BillingInvoice.created_at.desc())
            .limit(limit)
        ).all()
    )
    return [
        {
            "id": str(r.id),
            "source": "lokigi",
            "invoice_number": r.invoice_number,
            "period_start": r.period_start.isoformat(),
            "period_end": r.period_end.isoformat(),
            "plan": r.plan,
            "amount_usd": r.amount_cents / 100,
            "currency": r.currency,
            "status": r.status,
            "description": r.description,
            "has_pdf": bool(r.pdf_path),
            "pdf_url": f"/api/v1/subscription/invoices/{r.id}/pdf" if r.pdf_path else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def get_invoice_or_404(db: Session, user_id: UUID, invoice_id: UUID) -> BillingInvoice:
    inv = db.scalar(
        select(BillingInvoice).where(
            BillingInvoice.id == invoice_id,
            BillingInvoice.user_id == user_id,
        )
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return inv


def create_local_invoice(
    db: Session,
    user_id: UUID,
    plan: str,
    period_start: date,
    period_end: date,
    amount_cents: int,
    currency: str = "USD",
    description: str | None = None,
) -> BillingInvoice:
    """Create a BillingInvoice row; PDF is generated separately."""
    # Sequential invoice number per user
    count = db.scalar(
        select(func.count(BillingInvoice.id)).where(BillingInvoice.user_id == user_id)
    ) or 0
    invoice_number = f"LKG-{period_start.year}{period_start.month:02d}-{(count + 1):04d}"

    inv = BillingInvoice(
        id=uuid.uuid4(),
        user_id=user_id,
        invoice_number=invoice_number,
        period_start=period_start,
        period_end=period_end,
        plan=plan,
        amount_cents=amount_cents,
        currency=currency,
        status="paid",
        description=description,
    )
    db.add(inv)
    db.flush()
    return inv
