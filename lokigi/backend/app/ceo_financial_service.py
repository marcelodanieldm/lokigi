"""ceo_financial_service.py — MRR, Churn Rate, and LTV analytics for the CEO Command Center.

Data sources
────────────
• SubscriptionProfile  — plan, status, stripe_customer_id  (local DB)
• Stripe /v1/invoices  — paid amounts per customer per month  (Stripe API)
• LifecycleEvent       — churn_initiated events with created_at  (local DB)
• User.created_at      — cohort base for LTV calculation  (local DB)

All monetary values are returned in EUR/USD cents converted to float (€/$ units).

Cache strategy
──────────────
Results are serialised as JSON and stored in Redis with a TTL of 5 minutes.
If Redis is unavailable the functions compute fresh every time (graceful degradation).
"""

from __future__ import annotations

import json
import logging
from calendar import monthrange
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .models import LifecycleEvent, SubscriptionProfile, User

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Redis helper (optional)
# ──────────────────────────────────────────────────────────────────────────────

_redis_client = None

def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis  # type: ignore
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=2)
        _redis_client.ping()
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable — CEO cache disabled: %s", exc)
        return None


_CACHE_TTL = 300  # 5 minutes


def _cache_get(key: str) -> dict | None:
    r = _get_redis()
    if r is None:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def _cache_set(key: str, value: dict) -> None:
    r = _get_redis()
    if r is None:
        return
    try:
        r.setex(key, _CACHE_TTL, json.dumps(value, default=str))
    except Exception:
        pass


def _cache_invalidate(key: str) -> None:
    r = _get_redis()
    if r is None:
        return
    try:
        r.delete(key)
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Stripe helper
# ──────────────────────────────────────────────────────────────────────────────

_STRIPE_INVOICES = "https://api.stripe.com/v1/invoices"
_STRIPE_SUBS = "https://api.stripe.com/v1/subscriptions"


def _stripe_get(url: str, params: dict) -> list[dict]:
    """Fetch all pages of a Stripe list endpoint."""
    if not settings.stripe_secret_key:
        return []
    headers = {"Authorization": f"Bearer {settings.stripe_secret_key}"}
    results = []
    params = dict(params)
    params.setdefault("limit", 100)
    with httpx.Client(timeout=30) as client:
        while True:
            resp = client.get(url, headers=headers, params=params)
            if resp.status_code >= 400:
                logger.warning("Stripe %s returned %d", url, resp.status_code)
                break
            body = resp.json()
            results.extend(body.get("data", []))
            if not body.get("has_more"):
                break
            params["starting_after"] = results[-1]["id"]
    return results


# ──────────────────────────────────────────────────────────────────────────────
# MRR  — Monthly Recurring Revenue
# ──────────────────────────────────────────────────────────────────────────────

_ACTIVE_STATUSES = {"active", "trialing"}
_PLAN_PRICES: dict[str, float] = {
    "starter": 29.0,
    "growth": 79.0,
    "enterprise": 299.0,
}


def _local_mrr_breakdown(db: Session) -> dict[str, Any]:
    """Compute current MRR from local subscription profiles (no Stripe call needed)."""
    rows = db.execute(
        select(
            SubscriptionProfile.subscription_plan,
            func.count(SubscriptionProfile.id).label("count"),
        )
        .where(SubscriptionProfile.subscription_status.in_(list(_ACTIVE_STATUSES)))
        .group_by(SubscriptionProfile.subscription_plan)
    ).all()

    total = 0.0
    breakdown = {}
    for plan, count in rows:
        price = _PLAN_PRICES.get(plan, 0.0)
        subtotal = price * count
        breakdown[plan] = {"count": count, "price": price, "subtotal": subtotal}
        total += subtotal

    return {"total": total, "breakdown": breakdown}


def _stripe_monthly_revenue(months: int = 12) -> list[dict]:
    """Return aggregated paid invoice amounts per calendar month (last N months)."""
    from datetime import timedelta
    now = datetime.now(tz=timezone.utc)
    cutoff = int((now - timedelta(days=months * 31)).timestamp())

    invoices = _stripe_get(
        _STRIPE_INVOICES,
        {"status": "paid", "created[gte]": cutoff},
    )

    monthly: dict[str, float] = {}
    for inv in invoices:
        ts = inv.get("created")
        if not ts:
            continue
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        key = f"{dt.year}-{dt.month:02d}"
        monthly[key] = monthly.get(key, 0.0) + (inv.get("amount_paid", 0) / 100)

    # Produce an ordered list for the last `months` months
    result = []
    for i in range(months - 1, -1, -1):
        m_dt = _month_offset(now, -i)
        key = f"{m_dt.year}-{m_dt.month:02d}"
        result.append({"month": key, "revenue": round(monthly.get(key, 0.0), 2)})
    return result


def _month_offset(dt: datetime, delta_months: int) -> datetime:
    month = dt.month + delta_months
    year = dt.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


# ──────────────────────────────────────────────────────────────────────────────
# Churn Rate
# ──────────────────────────────────────────────────────────────────────────────


def _monthly_churn(db: Session, months: int = 12) -> list[dict]:
    """Churn rate per month = churns_in_month / active_at_start_of_month × 100."""
    now = datetime.now(tz=timezone.utc)
    result = []

    for i in range(months - 1, -1, -1):
        m_start = _month_offset(now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), -i)
        m_end = _month_offset(m_start, 1)
        month_key = f"{m_start.year}-{m_start.month:02d}"

        # Churns: LifecycleEvent with type 'churn_initiated' | 'cancellation_confirmed'
        churns = db.scalar(
            select(func.count(LifecycleEvent.id)).where(
                LifecycleEvent.event_type.in_(["churn_initiated", "cancellation_confirmed"]),
                LifecycleEvent.created_at >= m_start,
                LifecycleEvent.created_at < m_end,
            )
        ) or 0

        # Active subs at start of month (users created before start + not yet churned)
        active_at_start = db.scalar(
            select(func.count(SubscriptionProfile.id)).where(
                SubscriptionProfile.created_at < m_start,
                SubscriptionProfile.subscription_status.in_(list(_ACTIVE_STATUSES)),
            )
        ) or 0

        rate = round((churns / active_at_start * 100) if active_at_start > 0 else 0.0, 2)
        result.append({"month": month_key, "churns": churns, "active_base": active_at_start, "rate": rate})

    return result


# ──────────────────────────────────────────────────────────────────────────────
# LTV  — Lifetime Value
# ──────────────────────────────────────────────────────────────────────────────


def _compute_ltv(db: Session) -> dict[str, Any]:
    """LTV = ARPU / Churn Rate (monthly).

    ARPU (Average Revenue Per User) = MRR / active users.
    Monthly churn rate = average of last 3 months.
    """
    mrr_data = _local_mrr_breakdown(db)
    active_count = sum(v["count"] for v in mrr_data["breakdown"].values())
    mrr_total = mrr_data["total"]

    arpu = round(mrr_total / active_count, 2) if active_count else 0.0

    # Average churn rate from last 3 months (as a decimal, e.g. 0.03 = 3%)
    recent_churn = _monthly_churn(db, months=3)
    avg_churn_rate = sum(m["rate"] for m in recent_churn) / 3 / 100  # convert % → decimal

    ltv = round(arpu / avg_churn_rate, 2) if avg_churn_rate > 0 else None  # None = infinite (0 churn)

    return {
        "arpu": arpu,
        "avg_monthly_churn_rate_pct": round(avg_churn_rate * 100, 2),
        "ltv": ltv,
        "ltv_display": f"∞" if ltv is None else f"€{ltv:,.0f}",
        "active_users": active_count,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Plan mix
# ──────────────────────────────────────────────────────────────────────────────


def _plan_mix(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            SubscriptionProfile.subscription_plan,
            func.count(SubscriptionProfile.id).label("count"),
        ).group_by(SubscriptionProfile.subscription_plan)
    ).all()
    total = sum(r.count for r in rows) or 1
    return [
        {
            "plan": r.subscription_plan,
            "count": r.count,
            "pct": round(r.count / total * 100, 1),
        }
        for r in rows
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Main aggregator — returns everything the CEO dashboard needs
# ──────────────────────────────────────────────────────────────────────────────

_FINANCIALS_CACHE_KEY = "ceo:financials:v1"


def get_financial_kpis(db: Session, *, force_refresh: bool = False) -> dict[str, Any]:
    """Return full financial KPI payload, served from Redis cache when possible."""
    if not force_refresh:
        cached = _cache_get(_FINANCIALS_CACHE_KEY)
        if cached:
            return cached

    mrr = _local_mrr_breakdown(db)
    stripe_revenue = _stripe_monthly_revenue(months=12)
    churn_series = _monthly_churn(db, months=12)
    ltv = _compute_ltv(db)
    plan_mix = _plan_mix(db)

    # Total users
    total_users = db.scalar(select(func.count(User.id))) or 0

    # New users this month
    now = datetime.now(tz=timezone.utc)
    m_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_mtd = (
        db.scalar(select(func.count(User.id)).where(User.created_at >= m_start)) or 0
    )

    payload: dict[str, Any] = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "mrr": {
            "current": mrr["total"],
            "display": f"€{mrr['total']:,.0f}",
            "breakdown": mrr["breakdown"],
            "sparkline": [m["revenue"] for m in stripe_revenue],
            "sparkline_labels": [m["month"] for m in stripe_revenue],
        },
        "churn": {
            "current_rate_pct": churn_series[-1]["rate"] if churn_series else 0.0,
            "sparkline": [m["rate"] for m in churn_series],
            "sparkline_labels": [m["month"] for m in churn_series],
            "series": churn_series,
        },
        "ltv": ltv,
        "users": {
            "total": total_users,
            "new_mtd": new_users_mtd,
            "active": ltv["active_users"],
        },
        "plan_mix": plan_mix,
    }

    _cache_set(_FINANCIALS_CACHE_KEY, payload)
    return payload


def invalidate_financial_cache() -> None:
    _cache_invalidate(_FINANCIALS_CACHE_KEY)
