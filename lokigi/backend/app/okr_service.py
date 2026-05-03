"""okr_service.py — OKR Monitor: metric resolvers, progress calculation, seed data.

Metric sources
──────────────
Each OKRKeyResult.metric_source string maps to one of the METRIC_RESOLVERS functions
below.  These are auto-computed live from the database on every dashboard load.

Progress formula
────────────────
For direction='increase':
    progress_pct = clamp((current - baseline) / (target - baseline) * 100, 0, 100)

For direction='decrease':
    progress_pct = clamp((baseline - current) / (baseline - target) * 100, 0, 100)
    where target < baseline (we want to reduce toward target)

Objective progress
──────────────────
    Weighted average of all KR progress_pct values.

Seed data
─────────
`ensure_seed_okrs(db)` inserts Q2-2026 OKRs if the table is empty.
Safe to call on every startup.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    CustomerInsight,
    GoogleConnection,
    LifecycleEvent,
    MonthlyReport,
    OKRKeyResult,
    OKRObjective,
    Review,
    SubscriptionProfile,
    User,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Metric Resolvers  (db: Session) -> float
# ──────────────────────────────────────────────────────────────────────────────

MetricResolver = Callable[[Session], float]


def _count_users(db: Session) -> float:
    return float(db.scalar(select(func.count(User.id))) or 0)


def _count_active_subscriptions(db: Session) -> float:
    return float(
        db.scalar(
            select(func.count(SubscriptionProfile.id)).where(
                SubscriptionProfile.subscription_status.in_(["active", "trialing"])
            )
        ) or 0
    )


def _count_enterprise_plans(db: Session) -> float:
    return float(
        db.scalar(
            select(func.count(SubscriptionProfile.id)).where(
                SubscriptionProfile.subscription_plan == "enterprise",
                SubscriptionProfile.subscription_status.in_(["active", "trialing"]),
            )
        ) or 0
    )


def _count_growth_plans(db: Session) -> float:
    return float(
        db.scalar(
            select(func.count(SubscriptionProfile.id)).where(
                SubscriptionProfile.subscription_plan == "growth",
                SubscriptionProfile.subscription_status.in_(["active", "trialing"]),
            )
        ) or 0
    )


def _count_starter_plans(db: Session) -> float:
    return float(
        db.scalar(
            select(func.count(SubscriptionProfile.id)).where(
                SubscriptionProfile.subscription_plan == "starter",
                SubscriptionProfile.subscription_status.in_(["active", "trialing"]),
            )
        ) or 0
    )


def _count_google_connections(db: Session) -> float:
    return float(db.scalar(select(func.count(GoogleConnection.id))) or 0)


def _count_reviews_total(db: Session) -> float:
    return float(db.scalar(select(func.count(Review.id))) or 0)


def _count_reviews_replied(db: Session) -> float:
    return float(
        db.scalar(
            select(func.count(Review.id)).where(Review.reply_sent_at.is_not(None))
        ) or 0
    )


def _avg_response_rate_pct(db: Session) -> float:
    """Average response rate across all users (most recent StarterMonthlyMetrics row per user)."""
    from .models import StarterMonthlyMetrics
    from sqlalchemy import func as f

    # Latest year/month per user subquery
    latest_subq = (
        select(
            StarterMonthlyMetrics.user_id,
            func.max(StarterMonthlyMetrics.year * 100 + StarterMonthlyMetrics.month).label("ym"),
        )
        .group_by(StarterMonthlyMetrics.user_id)
        .subquery()
    )
    result = db.scalar(
        select(func.avg(StarterMonthlyMetrics.response_rate_pct))
        .join(
            latest_subq,
            (StarterMonthlyMetrics.user_id == latest_subq.c.user_id)
            & (
                (StarterMonthlyMetrics.year * 100 + StarterMonthlyMetrics.month)
                == latest_subq.c.ym
            ),
        )
    )
    return round(float(result or 0), 1)


def _count_upsell_candidates(db: Session) -> float:
    return float(
        db.scalar(
            select(func.count(CustomerInsight.id)).where(CustomerInsight.bucket == "upsell_candidate")
        ) or 0
    )


def _count_churn_risk(db: Session) -> float:
    return float(
        db.scalar(
            select(func.count(CustomerInsight.id)).where(CustomerInsight.bucket == "churn_risk")
        ) or 0
    )


def _count_lifecycle_churn_quarter(db: Session) -> float:
    """Churn events fired this calendar quarter."""
    now = datetime.now(tz=timezone.utc)
    q_start_month = ((now.month - 1) // 3) * 3 + 1
    q_start = now.replace(month=q_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    return float(
        db.scalar(
            select(func.count(LifecycleEvent.id)).where(
                LifecycleEvent.event_type.in_(["churn_initiated", "cancellation_confirmed"]),
                LifecycleEvent.created_at >= q_start,
            )
        ) or 0
    )


def _count_monthly_reports(db: Session) -> float:
    return float(db.scalar(select(func.count(MonthlyReport.id))) or 0)


METRIC_RESOLVERS: dict[str, MetricResolver] = {
    "count_users": _count_users,
    "count_active_subscriptions": _count_active_subscriptions,
    "count_enterprise_plans": _count_enterprise_plans,
    "count_growth_plans": _count_growth_plans,
    "count_starter_plans": _count_starter_plans,
    "count_google_connections": _count_google_connections,
    "count_reviews_total": _count_reviews_total,
    "count_reviews_replied": _count_reviews_replied,
    "avg_response_rate_pct": _avg_response_rate_pct,
    "count_upsell_candidates": _count_upsell_candidates,
    "count_churn_risk": _count_churn_risk,
    "count_lifecycle_churn_quarter": _count_lifecycle_churn_quarter,
    "count_monthly_reports": _count_monthly_reports,
    "manual": lambda _db: 0.0,  # sentinel — overridden by current_value_override
}


# ──────────────────────────────────────────────────────────────────────────────
# Progress helpers
# ──────────────────────────────────────────────────────────────────────────────


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def resolve_current_value(kr: OKRKeyResult, db: Session) -> float:
    """Return the current live value for a KR."""
    if kr.metric_source and kr.metric_source != "manual" and kr.metric_source in METRIC_RESOLVERS:
        try:
            return METRIC_RESOLVERS[kr.metric_source](db)
        except Exception:
            logger.exception("Metric resolver failed for %s", kr.metric_source)
    if kr.current_value_override is not None:
        return float(kr.current_value_override)
    return 0.0


def kr_progress_pct(kr: OKRKeyResult, current: float) -> float:
    """Return 0-100 progress percentage for a single KR."""
    target = float(kr.target_value)
    baseline = float(kr.baseline_value)

    if kr.direction == "decrease":
        span = baseline - target  # positive if target < baseline (going down)
        if span <= 0:
            return 100.0 if current <= target else 0.0
        return _clamp((baseline - current) / span * 100)
    else:  # increase
        span = target - baseline
        if span <= 0:
            return 100.0 if current >= target else 0.0
        return _clamp((current - baseline) / span * 100)


def objective_progress_pct(krs_with_progress: list[dict[str, Any]]) -> float:
    """Weighted average of KR progress values."""
    if not krs_with_progress:
        return 0.0
    total_weight = sum(kr["weight"] for kr in krs_with_progress)
    if total_weight == 0:
        return 0.0
    return round(
        sum(kr["progress_pct"] * kr["weight"] for kr in krs_with_progress) / total_weight, 1
    )


def _status_label(pct: float) -> str:
    if pct >= 90:
        return "on_track"
    if pct >= 60:
        return "at_risk"
    return "off_track"


def _status_color(label: str) -> str:
    return {"on_track": "#3fb950", "at_risk": "#d29922", "off_track": "#f85149"}.get(label, "#8b949e")


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard payload builder
# ──────────────────────────────────────────────────────────────────────────────


def build_okr_dashboard(db: Session, quarter: int | None = None, year: int | None = None) -> dict[str, Any]:
    """Return full OKR dashboard payload for the given quarter/year.

    If quarter/year are None, defaults to the current calendar quarter.
    """
    now = datetime.now(tz=timezone.utc)
    if year is None:
        year = now.year
    if quarter is None:
        quarter = (now.month - 1) // 3 + 1

    objectives = db.scalars(
        select(OKRObjective)
        .where(OKRObjective.quarter == quarter, OKRObjective.year == year, OKRObjective.is_active == True)
        .order_by(OKRObjective.sort_order, OKRObjective.created_at)
    ).all()

    result_objectives: list[dict[str, Any]] = []

    for obj in objectives:
        krs_payload: list[dict[str, Any]] = []
        for kr in obj.key_results:
            current = resolve_current_value(kr, db)
            pct = kr_progress_pct(kr, current)
            krs_payload.append(
                {
                    "id": str(kr.id),
                    "title": kr.title,
                    "unit": kr.unit,
                    "target_value": float(kr.target_value),
                    "baseline_value": float(kr.baseline_value),
                    "current_value": round(current, 1),
                    "metric_source": kr.metric_source,
                    "direction": kr.direction,
                    "progress_pct": round(pct, 1),
                    "weight": float(kr.weight),
                    "status": _status_label(pct),
                    "status_color": _status_color(_status_label(pct)),
                }
            )

        obj_pct = objective_progress_pct(krs_payload)
        obj_status = _status_label(obj_pct)
        result_objectives.append(
            {
                "id": str(obj.id),
                "title": obj.title,
                "description": obj.description,
                "owner": obj.owner,
                "sort_order": obj.sort_order,
                "progress_pct": round(obj_pct, 1),
                "status": obj_status,
                "status_color": _status_color(obj_status),
                "key_results": krs_payload,
            }
        )

    # Overall company score
    all_kr_weights = [kr for obj in result_objectives for kr in obj["key_results"]]
    overall = objective_progress_pct(all_kr_weights)

    return {
        "quarter": quarter,
        "year": year,
        "overall_pct": round(overall, 1),
        "overall_status": _status_label(overall),
        "overall_color": _status_color(_status_label(overall)),
        "objectives": result_objectives,
        "refreshed_at": now.isoformat(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Seed data — Q2 2026
# ──────────────────────────────────────────────────────────────────────────────

_SEED = [
    {
        "title": "Alcanzar masa crítica de locales conectados",
        "description": "Aumentar la base de clientes activos con Google Connection para construir un moat de datos.",
        "owner": "Growth",
        "sort_order": 0,
        "key_results": [
            {
                "title": "Alcanzar 100 locales con Plan Enterprise activos",
                "unit": "locales",
                "target_value": 100,
                "baseline_value": 0,
                "metric_source": "count_enterprise_plans",
                "direction": "increase",
                "weight": 2.0,
                "sort_order": 0,
            },
            {
                "title": "Superar 500 locales con Google Connection vinculada",
                "unit": "locales",
                "target_value": 500,
                "baseline_value": 0,
                "metric_source": "count_google_connections",
                "direction": "increase",
                "weight": 1.5,
                "sort_order": 1,
            },
            {
                "title": "Alcanzar 400 suscripciones activas totales",
                "unit": "usuarios",
                "target_value": 400,
                "baseline_value": 0,
                "metric_source": "count_active_subscriptions",
                "direction": "increase",
                "weight": 1.0,
                "sort_order": 2,
            },
        ],
    },
    {
        "title": "Reducir el Churn Rate por debajo del 3 %",
        "description": "Mejorar la retención de clientes mediante intervenciones tempranas y soporte proactivo.",
        "owner": "CEO",
        "sort_order": 1,
        "key_results": [
            {
                "title": "Menos de 15 eventos de churn en el trimestre",
                "unit": "eventos",
                "target_value": 15,
                "baseline_value": 40,
                "metric_source": "count_lifecycle_churn_quarter",
                "direction": "decrease",
                "weight": 2.0,
                "sort_order": 0,
            },
            {
                "title": "Reducir clientes en 'Riesgo de Churn' a menos de 10",
                "unit": "clientes",
                "target_value": 10,
                "baseline_value": 30,
                "metric_source": "count_churn_risk",
                "direction": "decrease",
                "weight": 1.5,
                "sort_order": 1,
            },
            {
                "title": "Convertir 40 clientes a 'Candidato a Upsell'",
                "unit": "clientes",
                "target_value": 40,
                "baseline_value": 0,
                "metric_source": "count_upsell_candidates",
                "direction": "increase",
                "weight": 1.0,
                "sort_order": 2,
            },
        ],
    },
    {
        "title": "Escalar la automatización de reseñas al 80 %",
        "description": "Demostrar ROI de la IA respondiendo la mayor parte de las reseñas de forma automática.",
        "owner": "Product",
        "sort_order": 2,
        "key_results": [
            {
                "title": "Responder automáticamente 80 % de las reseñas acumuladas",
                "unit": "%",
                "target_value": 80,
                "baseline_value": 0,
                "metric_source": "avg_response_rate_pct",
                "direction": "increase",
                "weight": 2.0,
                "sort_order": 0,
            },
            {
                "title": "Procesar 10 000 reseñas respondidas en total",
                "unit": "reseñas",
                "target_value": 10000,
                "baseline_value": 0,
                "metric_source": "count_reviews_replied",
                "direction": "increase",
                "weight": 1.0,
                "sort_order": 1,
            },
        ],
    },
    {
        "title": "Convertir el Plan Growth en el motor de ingresos principal",
        "description": "Impulsar upgrades de Starter → Growth para elevar el ARPU.",
        "owner": "Sales",
        "sort_order": 3,
        "key_results": [
            {
                "title": "Alcanzar 200 suscripciones en Plan Growth",
                "unit": "usuarios",
                "target_value": 200,
                "baseline_value": 0,
                "metric_source": "count_growth_plans",
                "direction": "increase",
                "weight": 2.0,
                "sort_order": 0,
            },
            {
                "title": "Generar 50 informes mensuales entregados",
                "unit": "informes",
                "target_value": 50,
                "baseline_value": 0,
                "metric_source": "count_monthly_reports",
                "direction": "increase",
                "weight": 1.0,
                "sort_order": 1,
            },
        ],
    },
]


def ensure_seed_okrs(db: Session) -> None:
    """Insert Q2-2026 seed OKRs if none exist. Idempotent."""
    count = db.scalar(select(func.count(OKRObjective.id)))
    if count and count > 0:
        return

    logger.info("Seeding OKR data for Q2-2026…")
    for item in _SEED:
        krs_data = item["key_results"]
        obj_data = {k: v for k, v in item.items() if k != "key_results"}
        obj = OKRObjective(
            id=uuid.uuid4(),
            quarter=2,
            year=2026,
            is_active=True,
            **obj_data,
        )
        db.add(obj)
        db.flush()
        for kr_data in krs_data:
            db.add(OKRKeyResult(id=uuid.uuid4(), objective_id=obj.id, **kr_data))

    db.commit()
    logger.info("OKR seed complete — %d objectives inserted", len(_SEED))
