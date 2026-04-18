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

import json
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from .config import settings
from .database import engine
from .models import GoogleConnection, MonthlyReport, Review, StarterMonthlyMetrics, User
from .sentiment_analysis import analyze_monthly_sentiment

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler factory
# ─────────────────────────────────────────────────────────────────────────────

def build_scheduler() -> AsyncIOScheduler:
    """Return an ``AsyncIOScheduler`` with the monthly-report job registered."""
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_monthly_reports,
        trigger=CronTrigger(day=1, hour=6, minute=0),
        id="monthly_report_job",
        name="Generate monthly reports for all active users",
        replace_existing=True,
        misfire_grace_time=3600,  # tolerate up to 1h delay (e.g. server restart)
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
    payload = _build_report_payload(
        user_id=user.id,
        location_id=conn.location_id,
        business_name=conn.business_name or conn.location_id,
        year=year,
        month=month,
        kpis=kpis,
        sentiment=sentiment,
    )
    _upsert_report(db, user.id, year, month, payload)
    db.commit()

    if settings.sendgrid_api_key and user.email:
        await _send_report_email(
            to_email=user.email,
            business_name=payload["business_name"],
            year=year,
            month=month,
            kpis=kpis,
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
) -> dict[str, Any]:
    return {
        "report_id": str(uuid.uuid4()),
        "user_id": str(user_id),
        "location_id": location_id,
        "business_name": business_name,
        "period": {"year": year, "month": month},
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "kpis": kpis,
        "sentiment": {
            "positive_concepts": sentiment.get("positive_concepts", []),
            "negative_concepts": sentiment.get("negative_concepts", []),
            "chart_data": sentiment.get("chart_data", {}),
        },
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
) -> None:
    subject = f"Tu Reporte Mensual Lokigi — {_month_label(month)} {year}"
    total = kpis.get("total_reviews", 0)
    avg_rating = kpis.get("avg_rating")
    response_rate = kpis.get("response_rate_pct")

    avg_rating_str = f"{avg_rating:.1f} ★" if avg_rating is not None else "—"
    response_rate_str = f"{response_rate:.0f}%" if response_rate is not None else "—"

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
      <p>Tu reporte de <strong>{business_name}</strong> para <strong>{_month_label(month)} {year}</strong> ya está listo.</p>

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

      <p style="color:#6b7280;font-size:14px">
        Inicia sesión en Lokigi para ver el análisis completo de sentimiento, los conceptos más mencionados y el gráfico de barras interactivo.
      </p>
      <div style="text-align:center;margin:28px 0">
        <a href="https://{settings.app_domain}/starter/dashboard"
           style="background:#1a56db;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:15px">
          Ver reporte completo →
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
