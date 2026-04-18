from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import GoogleConnection, SubscriptionProfile


def get_or_create_subscription_profile(db: Session, user_id: UUID) -> SubscriptionProfile:
    profile = db.scalar(select(SubscriptionProfile).where(SubscriptionProfile.user_id == user_id))
    if profile:
        return profile

    profile = SubscriptionProfile(user_id=user_id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _stripe_headers() -> dict[str, str]:
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")
    return {
        "Authorization": f"Bearer {settings.stripe_secret_key}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def _safe_dt_from_epoch(value: int | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _status_label(status: str) -> str:
    mapping = {
        "active": "Activa",
        "trialing": "Activa",
        "canceled": "Cancelada",
        "cancelled": "Cancelada",
        "past_due": "En mora",
        "unpaid": "En mora",
        "incomplete_expired": "Cancelada",
        "incomplete": "Pendiente",
    }
    return mapping.get((status or "active").lower(), "Activa")


def sync_subscription_from_stripe(db: Session, profile: SubscriptionProfile) -> SubscriptionProfile:
    if not settings.stripe_secret_key or not profile.stripe_subscription_id:
        return profile

    headers = {"Authorization": f"Bearer {settings.stripe_secret_key}"}
    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            f"https://api.stripe.com/v1/subscriptions/{profile.stripe_subscription_id}",
            headers=headers,
        )
    if response.status_code >= 400:
        return profile

    payload = response.json()
    profile.subscription_status = payload.get("status") or profile.subscription_status
    profile.current_period_end = _safe_dt_from_epoch(payload.get("current_period_end"))
    db.commit()
    db.refresh(profile)
    return profile


def get_subscription_summary(db: Session, user_id: UUID) -> dict[str, Any]:
    profile = get_or_create_subscription_profile(db, user_id)
    profile = sync_subscription_from_stripe(db, profile)

    return {
        "plan": profile.subscription_plan,
        "status": profile.subscription_status,
        "status_label": _status_label(profile.subscription_status),
        "current_period_end": profile.current_period_end.isoformat() if profile.current_period_end else None,
        "stripe_configured": bool(settings.stripe_secret_key),
        "has_customer": bool(profile.stripe_customer_id),
        "has_subscription": bool(profile.stripe_subscription_id),
    }


def list_subscription_invoices(db: Session, user_id: UUID, limit: int = 12) -> list[dict[str, Any]]:
    profile = get_or_create_subscription_profile(db, user_id)
    if not settings.stripe_secret_key or not profile.stripe_customer_id:
        return []

    headers = {"Authorization": f"Bearer {settings.stripe_secret_key}"}
    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            "https://api.stripe.com/v1/invoices",
            headers=headers,
            params={"customer": profile.stripe_customer_id, "limit": limit},
        )
    if response.status_code >= 400:
        return []

    invoices = []
    for invoice in response.json().get("data", []):
        invoices.append(
            {
                "id": invoice.get("id"),
                "number": invoice.get("number") or invoice.get("id"),
                "status": invoice.get("status") or "paid",
                "amount_paid": (invoice.get("amount_paid") or 0) / 100,
                "currency": (invoice.get("currency") or "usd").upper(),
                "created_at": _safe_dt_from_epoch(invoice.get("created")).isoformat() if invoice.get("created") else None,
                "invoice_pdf": invoice.get("invoice_pdf"),
                "hosted_invoice_url": invoice.get("hosted_invoice_url"),
            }
        )
    return invoices


def get_growth_upsell_url(user_id: UUID) -> str:
    if settings.stripe_growth_checkout_url:
        return settings.stripe_growth_checkout_url
    return f"/starter/subscription?user_id={user_id}&upsell=growth"


def create_growth_checkout_session(db: Session, user_id: UUID) -> dict[str, Any]:
    profile = get_or_create_subscription_profile(db, user_id)
    if settings.stripe_growth_checkout_url:
        return {"checkout_url": settings.stripe_growth_checkout_url, "source": "configured_url"}

    if not settings.stripe_secret_key or not settings.stripe_growth_price_id:
        return {"checkout_url": get_growth_upsell_url(user_id), "source": "fallback"}

    data: dict[str, Any] = {
        "mode": "subscription",
        "success_url": f"https://{settings.app_domain}/starter/subscription?user_id={user_id}&upgrade=success",
        "cancel_url": f"https://{settings.app_domain}/starter/subscription?user_id={user_id}&upsell=growth",
        "line_items[0][price]": settings.stripe_growth_price_id,
        "line_items[0][quantity]": "1",
        "client_reference_id": str(user_id),
    }
    if profile.stripe_customer_id:
        data["customer"] = profile.stripe_customer_id
    else:
        connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
        if connection:
            data["customer_email"] = connection.user.email if connection.user else ""

    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            headers=_stripe_headers(),
            data=data,
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Unable to create Stripe checkout session")

    payload = response.json()
    return {"checkout_url": payload.get("url"), "source": "stripe_checkout"}


def check_growth_upgrade_needed(db: Session, user_id: UUID, requested_location_id: str) -> dict[str, Any]:
    profile = get_or_create_subscription_profile(db, user_id)
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))

    if not connection:
        return {"upgrade_required": False, "reason": "no_existing_connection"}

    requested = (requested_location_id or "").strip()
    if not requested or requested == connection.location_id:
        return {"upgrade_required": False, "reason": "same_or_missing_location"}

    if profile.subscription_plan.lower() != "starter":
        return {"upgrade_required": False, "reason": "plan_allows_multiple_locations"}

    return {
        "upgrade_required": True,
        "target_plan": "growth",
        "reason": "starter_single_location_limit",
        "current_location_id": connection.location_id,
        "requested_location_id": requested,
        "message": "El Plan Starter incluye una sola ubicación. Para añadir una segunda ubicación necesitas actualizar a Growth.",
        "upsell": {
            "title": "Desbloquea múltiples ubicaciones con Growth",
            "body": "Growth te permite conectar más de una ubicación, centralizar reputación multi-sede y escalar la automatización.",
            "cta_label": "Actualizar a Growth",
            "cta_url": get_growth_upsell_url(user_id),
        },
    }
