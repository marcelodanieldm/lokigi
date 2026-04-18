"""monthly_report_worker.py
Cron job that runs on day 1 of every month.

Flow per active user
────────────────────
1. Pull KPIs from ``starter_monthly_metrics`` (already populated by the
   nightly upsert job).  If no row exists for the target month the KPIs
   are computed on-the-fly from raw reviews so the report is never empty.
2. Fetch all reviews for the target month and run the sentiment engine.
3. Assemble a structured ``MonthlyReport`` JSON payload.
4. Persist the report to the ``monthly_reports`` table (idempotent: one
   report per user/year/month — existing row is updated rather than inserted
   again so the job is safe to re-run).
5. Send a "your report is ready" notification e-mail via the SendGrid
   REST API (no SDK – uses the ``httpx`` client already in the project).

Scheduler wiring
────────────────
``build_scheduler()`` returns a configured ``AsyncIOScheduler`` that the
FastAPI lifespan starts/stops.  The cron trigger fires at 06:00 UTC on the
1st of every month.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from .auto_reply_worker import run_auto_reply_dispatch
from .config import settings
from .database import engine
from .growth_premium_report_service import GrowthPremiumReportService, PremiumConfig
from .growth_sentiment_benchmark_service import BenchmarkConfig, GrowthSentimentBenchmarkService
from .models import GoogleConnection, GrowthCompetitor, MonthlyReport, Review, StarterMonthlyMetrics, User
from .sentiment_analysis import analyze_monthly_sentiment

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler factory
# ─────────────────────────────────────────────────────────────────────────────

def build_scheduler() -> AsyncIOScheduler:
    """Return an ``AsyncIOScheduler`` with the monthly-report job registered."""
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_auto_reply_dispatch,
        trigger=IntervalTrigger(minutes=1),
        id="auto_reply_dispatch_job",
        name="Dispatch pending auto replies",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )
    scheduler.add_job(
        run_monthly_reports,
        trigger=CronTrigger(day=1, hour=6, minute=0),
        id="monthly_report_job",
        name="Generate monthly reports for all active users",
        replace_existing=True,
        misfire_grace_time=3600,  # tolerate up to 1h delay (e.g. server restart)
    )
    scheduler.add_job(
        run_growth_sentiment_benchmark_daily,
        trigger=CronTrigger(hour=7, minute=15),
        id="growth_sentiment_benchmark_daily_job",
        name="Run Growth sentiment benchmark daily",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=1800,
    )
    return scheduler


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point (called by the scheduler)
# ─────────────────────────────────────────────────────────────────────────────

async def run_monthly_reports() -> None:
    """Process monthly reports for every user that has an active Google
    connection.  Reports are for the *previous* calendar month.
    """
    today = date.today()
    year, month = _previous_month(today.year, today.month)
    logger.info("Monthly report job started — period %04d-%02d", year, month)

    with Session(engine) as db:
        users = db.scalars(select(User)).all()
        for user in users:
            try:
                conn = db.scalars(
                    select(GoogleConnection).where(GoogleConnection.user_id == user.id)
                ).first()
                if conn is None:
                    continue  # user never connected Google — skip
                await _process_user(db, user, conn, year, month)
            except Exception:
                logger.exception("Monthly report failed for user %s", user.id)

    logger.info("Monthly report job finished — period %04d-%02d", year, month)


async def run_growth_sentiment_benchmark_daily() -> None:
    """Compute daily sentiment benchmarking for users with active Growth competitors."""
    logger.info("Growth sentiment benchmark daily job started")

    with Session(engine) as db:
        user_ids = db.scalars(
            select(GrowthCompetitor.user_id)
            .where(GrowthCompetitor.is_active.is_(True))
            .distinct()
        ).all()

        service = GrowthSentimentBenchmarkService(db)
        cfg = BenchmarkConfig()
        for user_id in user_ids:
            try:
                service.run_for_user(user_id=user_id, config=cfg)
            except Exception:
                db.rollback()
                logger.exception("Growth sentiment benchmark failed for user %s", user_id)

    logger.info("Growth sentiment benchmark daily job finished")


# ─────────────────────────────────────────────────────────────────────────────
# Per-user processing
# ─────────────────────────────────────────────────────────────────────────────

async def _process_user(
    db: Session,
    user: User,
    conn: GoogleConnection,
    year: int,
    month: int,
) -> None:
    kpis = _fetch_kpis(db, user.id, conn.location_id, year, month)
    sentiment = _fetch_sentiment(db, conn, year, month)
    value_metrics = _build_value_metrics(db, user.id, conn, year, month, sentiment)
    growth_premium = _build_growth_premium_payload(db, user.id)
    payload = _build_report_payload(
        user_id=user.id,
        location_id=conn.location_id,
        business_name=conn.business_name or conn.location_id,
        year=year,
        month=month,
        kpis=kpis,
        sentiment=sentiment,
        value_metrics=value_metrics,
        growth_premium=growth_premium,
    )
    report_row = _upsert_report(db, user.id, year, month, payload)
    db.commit()

    await _enqueue_pdf_generation(report_row.id)
    pdf_url = await _await_pdf_signed_url(db, report_row.id)
    report_online_url = _build_report_online_url(user.id, year, month)

    if settings.sendgrid_api_key and user.email:
        await _send_report_email(
            to_email=user.email,
            business_name=payload["business_name"],
            year=year,
            month=month,
            kpis=kpis,
            pdf_url=pdf_url,
            report_online_url=report_online_url,
        )


# ─────────────────────────────────────────────────────────────────────────────
# KPI collection
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_kpis(
    db: Session,
    user_id: uuid.UUID,
    location_id: str,
    year: int,
    month: int,
) -> dict[str, Any]:
    """Return KPI dict.  Prefers pre-aggregated row; falls back to live query."""
    row = db.scalars(
        select(StarterMonthlyMetrics).where(
            StarterMonthlyMetrics.user_id == user_id,
            StarterMonthlyMetrics.year == year,
            StarterMonthlyMetrics.month == month,
        )
    ).first()

    if row:
        return {
            "total_reviews": row.total_reviews,
            "avg_rating": float(row.avg_rating) if row.avg_rating is not None else None,
            "response_rate_pct": float(row.response_rate_pct) if row.response_rate_pct is not None else None,
            "avg_response_time_minutes": float(row.avg_response_time_minutes) if row.avg_response_time_minutes is not None else None,
        }

    # Fall-back: compute on-the-fly from raw reviews
    reviews = _get_month_reviews(db, user_id, year, month)
    total = len(reviews)
    if total == 0:
        return {
            "total_reviews": 0,
            "avg_rating": None,
            "response_rate_pct": None,
            "avg_response_time_minutes": None,
        }

    ratings = [r.rating for r in reviews if r.rating is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
    auto_replies = sum(1 for r in reviews if r.reply_action == "AUTO_REPLY")
    response_rate = round(auto_replies / total * 100, 2) if total else None

    response_times = [
        (r.reply_decided_at - r.create_time).total_seconds() / 60
        for r in reviews
        if r.reply_decided_at is not None and r.create_time is not None
    ]
    avg_resp_time = round(sum(response_times) / len(response_times), 2) if response_times else None

    return {
        "total_reviews": total,
        "avg_rating": avg_rating,
        "response_rate_pct": response_rate,
        "avg_response_time_minutes": avg_resp_time,
    }


def _get_month_reviews(
    db: Session,
    user_id: uuid.UUID,
    year: int,
    month: int,
) -> list[Review]:
    return list(
        db.scalars(
            select(Review)
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(
                GoogleConnection.user_id == user_id,
                extract("year", Review.create_time) == year,
                extract("month", Review.create_time) == month,
            )
        ).all()
    )


def _normalize_dt(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _minutes_between(start: datetime | None, end: datetime | None) -> float | None:
    start_dt = _normalize_dt(start)
    end_dt = _normalize_dt(end)
    if start_dt is None or end_dt is None:
        return None
    delta = (end_dt - start_dt).total_seconds() / 60
    return round(delta, 2) if delta >= 0 else None


def _extract_pre_lokigi_reply_timestamp(review: Review) -> datetime | None:
    raw = review.raw_payload or {}
    reply_payload = raw.get("reviewReply") or raw.get("ownerReply") or {}
    if not isinstance(reply_payload, dict):
        return None
    return _normalize_dt(
        reply_payload.get("updateTime")
        or reply_payload.get("createTime")
        or reply_payload.get("lastModifiedTime")
    )


def _average_minutes(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _build_response_velocity(db: Session, user_id: uuid.UUID, conn: GoogleConnection, year: int, month: int) -> dict[str, Any]:
    current_reviews = _get_month_reviews(db, user_id, year, month)
    current_deltas = [
        minutes
        for review in current_reviews
        for minutes in [_minutes_between(review.create_time, review.reply_sent_at or review.reply_decided_at)]
        if minutes is not None
    ]
    current_avg = _average_minutes(current_deltas)

    historical_reviews = list(
        db.scalars(
            select(Review)
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(
                GoogleConnection.user_id == user_id,
                Review.create_time.is_not(None),
                Review.create_time < conn.created_at,
            )
            .order_by(Review.create_time.desc())
            .limit(500)
        ).all()
    )

    baseline_deltas = [
        minutes
        for review in historical_reviews
        for minutes in [_minutes_between(review.create_time, _extract_pre_lokigi_reply_timestamp(review))]
        if minutes is not None
    ]

    baseline_source = "google_history"
    baseline_avg = _average_minutes(baseline_deltas)
    if baseline_avg is None:
        baseline_avg = 1440.0
        baseline_source = "reference_24h"

    improvement_pct = None
    delta_minutes = None
    if current_avg is not None and baseline_avg:
        delta_minutes = round(baseline_avg - current_avg, 2)
        improvement_pct = round(((baseline_avg - current_avg) / baseline_avg) * 100, 1)

    return {
        "current_avg_minutes": current_avg,
        "baseline_avg_minutes": baseline_avg,
        "delta_minutes": delta_minutes,
        "improvement_pct": improvement_pct,
        "current_sample_size": len(current_deltas),
        "baseline_sample_size": len(baseline_deltas),
        "baseline_source": baseline_source,
        "current_label": "Promedio de Lokigi",
        "baseline_label": "Antes de Lokigi" if baseline_source == "google_history" else "Referencia manual previa",
    }


def _build_value_metrics(
    db: Session,
    user_id: uuid.UUID,
    conn: GoogleConnection,
    year: int,
    month: int,
    sentiment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "response_velocity": _build_response_velocity(db, user_id, conn, year, month),
        "sentiment_snapshot": sentiment.get("sentiment_snapshot", {}),
        "keyword_cloud": {
            "top_concepts": sentiment.get("top_concepts", [])[:5],
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Sentiment
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_sentiment(
    db: Session,
    conn: GoogleConnection,
    year: int,
    month: int,
) -> dict[str, Any]:
    reviews = _get_month_reviews(db, conn.user_id, year, month)
    review_dicts = [{"rating": r.rating, "comment": r.comment or ""} for r in reviews]
    report = analyze_monthly_sentiment(
        review_dicts,
        year=year,
        month=month,
        location_id=conn.location_id,
    )
    return report.to_dict()


# ─────────────────────────────────────────────────────────────────────────────
# Report payload builder  (pure function — easy to test in isolation)
# ─────────────────────────────────────────────────────────────────────────────

def _build_report_payload(
    *,
    user_id: uuid.UUID,
    location_id: str,
    business_name: str,
    year: int,
    month: int,
    kpis: dict[str, Any],
    sentiment: dict[str, Any],
    value_metrics: dict[str, Any],
    growth_premium: dict[str, Any],
) -> dict[str, Any]:
    return {
        "report_id": str(uuid.uuid4()),
        "user_id": str(user_id),
        "location_id": location_id,
        "business_name": business_name,
        "period": {"year": year, "month": month},
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "kpis": kpis,
        "value_metrics": value_metrics,
        "growth_premium": growth_premium,
        "sentiment": {
            "total_reviews_analyzed": sentiment.get("total_reviews_analyzed", 0),
            "positive_reviews": sentiment.get("positive_reviews", 0),
            "positive_concepts": sentiment.get("positive_concepts", []),
            "neutral_reviews": sentiment.get("neutral_reviews", 0),
            "negative_reviews": sentiment.get("negative_reviews", 0),
            "negative_concepts": sentiment.get("negative_concepts", []),
            "top_concepts": sentiment.get("top_concepts", []),
            "sentiment_snapshot": sentiment.get("sentiment_snapshot", {}),
            "chart_data": sentiment.get("chart_data", {}),
        },
    }


def _build_growth_premium_payload(db: Session, user_id: uuid.UUID) -> dict[str, Any]:
    try:
        service = GrowthPremiumReportService(db)
        return service.build_report(
            user_id=user_id,
            config=PremiumConfig(window_days=30, max_locations=5),
        )
    except Exception:
        logger.exception("Growth premium payload build failed for user %s", user_id)
        return {
            "status": "unavailable",
            "reason": "growth_premium_build_failed",
        }


# ─────────────────────────────────────────────────────────────────────────────
# DB persistence (upsert)
# ─────────────────────────────────────────────────────────────────────────────

def _upsert_report(
    db: Session,
    user_id: uuid.UUID,
    year: int,
    month: int,
    payload: dict[str, Any],
) -> MonthlyReport:
    existing = db.scalars(
        select(MonthlyReport).where(
            MonthlyReport.user_id == user_id,
            MonthlyReport.year == year,
            MonthlyReport.month == month,
        )
    ).first()

    if existing:
        existing.payload = payload
        existing.generated_at = datetime.now(tz=timezone.utc)
        existing.pdf_status = "pending"
        existing.pdf_object_key = None
        existing.pdf_signed_url = None
        existing.pdf_signed_url_expires_at = None
        existing.pdf_generated_at = None
        existing.pdf_error = None
        db.add(existing)
        return existing

    report = MonthlyReport(
        user_id=user_id,
        year=year,
        month=month,
        payload=payload,
        generated_at=datetime.now(tz=timezone.utc),
    )
    db.add(report)
    return report


async def _enqueue_pdf_generation(report_id: uuid.UUID) -> None:
    """Request async PDF render through external BullMQ worker endpoint."""
    if not settings.pdf_worker_enqueue_url:
        logger.info("PDF enqueue URL not configured, skipping PDF generation for report %s", report_id)
        return

    headers = {"Content-Type": "application/json"}
    if settings.pdf_worker_enqueue_token:
        headers["X-Worker-Token"] = settings.pdf_worker_enqueue_token

    body = {
        "report_id": str(report_id),
        "requested_at": datetime.now(tz=timezone.utc).isoformat(),
        "signed_url_ttl_seconds": settings.pdf_signed_url_ttl_seconds,
    }

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(settings.pdf_worker_enqueue_url, headers=headers, json=body)
            if response.status_code not in (200, 201, 202):
                logger.error(
                    "Failed to enqueue monthly report PDF %s (status=%s): %s",
                    report_id,
                    response.status_code,
                    response.text[:240],
                )
            else:
                logger.info("Queued monthly report PDF generation for report %s", report_id)
    except Exception:
        logger.exception("Unexpected error enqueueing PDF generation for report %s", report_id)


# ─────────────────────────────────────────────────────────────────────────────
# E-mail via SendGrid REST API  (uses httpx — no SDK)
# ─────────────────────────────────────────────────────────────────────────────

_SENDGRID_SEND_URL = "https://api.sendgrid.com/v3/mail/send"


async def _send_report_email(
    *,
    to_email: str,
    business_name: str,
    year: int,
    month: int,
    kpis: dict[str, Any],
    pdf_url: str | None = None,
    report_online_url: str | None = None,
) -> None:
    subject = f"Tu reporte de exito de {business_name} ya esta disponible - {_month_label(month)} {year}"
    total = kpis.get("total_reviews", 0)
    avg_rating = kpis.get("avg_rating")
    response_rate = kpis.get("response_rate_pct")

    avg_rating_str = f"{avg_rating:.1f} ★" if avg_rating is not None else "-"
    response_rate_str = f"{response_rate:.0f}%" if response_rate is not None else "-"
    effective_report_url = report_online_url or f"https://{settings.app_domain}/starter/dashboard"
    pdf_button_html = ""
    if pdf_url:
        pdf_button_html = f"""
      <div style="text-align:center;margin:28px 0 12px">
        <a href="{pdf_url}"
           style="background:#1a56db;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:15px">
          Descargar PDF
        </a>
      </div>
        """

    html_body = f"""
<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>{subject}</title></head>
<body style="font-family:Arial,sans-serif;background:#f4f6f9;padding:32px">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1)">
    <div style="background:#1a56db;padding:24px 32px">
      <h1 style="color:#fff;margin:0;font-size:22px">Lokigi</h1>
      <p style="color:#cce0ff;margin:4px 0 0">Reporte Mensual</p>
    </div>
    <div style="padding:32px">
      <p style="font-size:16px">Hola,</p>
            <p>Tu reporte de exito de <strong>{business_name}</strong> para <strong>{_month_label(month)} {year}</strong> ya esta disponible.</p>

      <table style="width:100%;border-collapse:collapse;margin:24px 0">
        <tr style="background:#f0f4ff">
          <td style="padding:12px 16px;font-weight:bold;color:#374151">Total de reseñas</td>
          <td style="padding:12px 16px;text-align:right;font-size:20px;font-weight:bold;color:#1a56db">{total}</td>
        </tr>
        <tr>
          <td style="padding:12px 16px;font-weight:bold;color:#374151">Calificación promedio</td>
          <td style="padding:12px 16px;text-align:right;font-size:20px;font-weight:bold;color:#1a56db">{avg_rating_str}</td>
        </tr>
        <tr style="background:#f0f4ff">
          <td style="padding:12px 16px;font-weight:bold;color:#374151">Tasa de respuesta</td>
          <td style="padding:12px 16px;text-align:right;font-size:20px;font-weight:bold;color:#1a56db">{response_rate_str}</td>
        </tr>
      </table>

            {pdf_button_html}

      <p style="color:#6b7280;font-size:14px">
        Inicia sesión en Lokigi para ver el análisis completo de sentimiento, los conceptos más mencionados y el gráfico de barras interactivo.
      </p>
      <div style="text-align:center;margin:28px 0">
                <a href="{effective_report_url}"
           style="background:#1a56db;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:15px">
                    Ver Online →
        </a>
      </div>
    </div>
    <div style="background:#f9fafb;padding:16px 32px;text-align:center;font-size:12px;color:#9ca3af">
      Lokigi · {settings.app_domain} · Responde este email para soporte
    </div>
  </div>
</body>
</html>
"""

    body = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": settings.sendgrid_from_email, "name": "Lokigi"},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_body}],
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            _SENDGRID_SEND_URL,
            headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            json=body,
        )
        if response.status_code not in (200, 202):
            logger.error(
                "SendGrid error %s for user %s: %s",
                response.status_code,
                to_email,
                response.text[:200],
            )
        else:
            logger.info("Report email sent to %s (%04d-%02d)", to_email, year, month)


def _build_report_online_url(user_id: uuid.UUID, year: int, month: int) -> str:
    return f"https://{settings.app_domain}/starter/report?user_id={user_id}&year={year}&month={month}"


async def _await_pdf_signed_url(db: Session, report_id: uuid.UUID, timeout_seconds: int = 120) -> str | None:
    """Wait briefly for async PDF worker to attach a signed URL to the monthly report row."""
    if not settings.pdf_worker_enqueue_url:
        return None

    deadline = datetime.now(tz=timezone.utc).timestamp() + timeout_seconds
    while datetime.now(tz=timezone.utc).timestamp() < deadline:
        db.expire_all()
        row = db.scalars(select(MonthlyReport).where(MonthlyReport.id == report_id)).first()
        if not row:
            return None
        if row.pdf_status == "ready" and row.pdf_signed_url:
            return row.pdf_signed_url
        if row.pdf_status == "failed":
            return None
        await asyncio.sleep(4)

    logger.warning("Timed out waiting for PDF URL for report %s", report_id)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _previous_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


_MONTH_LABELS_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _month_label(month: int) -> str:
    return _MONTH_LABELS_ES.get(month, str(month))
