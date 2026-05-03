"""customer_health_service.py — Customer Health Score algorithm for the Executive CRM.

Score composition (0-100)
──────────────────────────
  login_score         0-40   Platform activity recency (UserSession or GoogleConnection.updated_at)
  response_rate_score 0-35   % of reviews with reply_sent_at  →  0 %=0, 100 %=35
  ranking_score       0-25   SERP rank improvement vs 30 days ago

Buckets
───────
  score >= 80  →  upsell_candidate
  score <  30  →  churn_risk
  else         →  healthy

Usage
─────
  from app.customer_health_service import compute_health_score, recompute_all_insights
  record = compute_health_score(db, user_id)
  recompute_all_insights(db)          # nightly batch
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    CustomerInsight,
    GoogleConnection,
    GrowthSerpObservation,
    Review,
    SubscriptionProfile,
    User,
    UserSession,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

_LOOKBACK_DAYS = 30
_MAX_LOGIN_SCORE = 40
_MAX_RESPONSE_SCORE = 35
_MAX_RANKING_SCORE = 25

_BUCKET_UPSELL = "upsell_candidate"
_BUCKET_CHURN = "churn_risk"
_BUCKET_HEALTHY = "healthy"


# ──────────────────────────────────────────────────────────────────────────────
# Sub-score helpers
# ──────────────────────────────────────────────────────────────────────────────


def _login_sub_score(db: Session, user_id: UUID) -> tuple[int, int | None]:
    """Return (score 0-40, days_since_last_activity).

    Primary source: UserSession (created_at).
    Fallback: GoogleConnection.updated_at (token refresh = implicit activity).
    """
    now = datetime.now(tz=timezone.utc)

    # Last explicit session
    last_session = db.scalar(
        select(func.max(UserSession.created_at)).where(UserSession.user_id == user_id)
    )

    # Fallback: connection token updated_at
    last_conn = db.scalar(
        select(func.max(GoogleConnection.updated_at)).where(GoogleConnection.user_id == user_id)
    )

    last_activity = max(
        filter(None, [last_session, last_conn]),
        default=None,
    )

    if last_activity is None:
        return 0, None

    days = (now - last_activity).days if last_activity.tzinfo else (now - last_activity.replace(tzinfo=timezone.utc)).days

    # Scoring curve:
    #   0 days  → 40   (active today)
    #   7 days  → 32
    #  14 days  → 20
    #  30 days  →  8
    #  >60 days →  0
    if days <= 1:
        score = 40
    elif days <= 7:
        score = int(40 - (days - 1) * (40 - 32) / 6)
    elif days <= 14:
        score = int(32 - (days - 7) * (32 - 20) / 7)
    elif days <= 30:
        score = int(20 - (days - 14) * (20 - 8) / 16)
    elif days <= 60:
        score = int(8 - (days - 30) * 8 / 30)
    else:
        score = 0

    return max(0, min(_MAX_LOGIN_SCORE, score)), days


def _response_rate_sub_score(db: Session, user_id: UUID) -> tuple[int, float | None]:
    """Return (score 0-35, response_rate_pct)."""
    # Reviews in last 90 days for this user's connection
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=90)

    gc = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    if gc is None:
        return 0, None

    total = db.scalar(
        select(func.count(Review.id)).where(
            Review.connection_id == gc.id,
            Review.create_time >= cutoff,
        )
    ) or 0

    if total == 0:
        return 0, None

    responded = db.scalar(
        select(func.count(Review.id)).where(
            Review.connection_id == gc.id,
            Review.create_time >= cutoff,
            Review.reply_sent_at.is_not(None),
        )
    ) or 0

    rate_pct = round(responded / total * 100, 1)
    # Linear: 100 % → 35, 0 % → 0
    score = int(rate_pct / 100 * _MAX_RESPONSE_SCORE)
    return min(_MAX_RESPONSE_SCORE, score), rate_pct


def _ranking_sub_score(db: Session, user_id: UUID) -> tuple[int, int | None]:
    """Return (score 0-25, rank_delta).

    rank_delta = current_rank - rank_30d_ago  (negative = improvement)
    """
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(days=_LOOKBACK_DAYS)

    # Latest observation (client entity only)
    latest_rank = db.scalar(
        select(GrowthSerpObservation.rank_position)
        .where(
            GrowthSerpObservation.user_id == user_id,
            GrowthSerpObservation.entity_type == "client",
        )
        .order_by(GrowthSerpObservation.observed_at.desc())
        .limit(1)
    )

    # Oldest observation in the 30-day window
    oldest_rank = db.scalar(
        select(GrowthSerpObservation.rank_position)
        .where(
            GrowthSerpObservation.user_id == user_id,
            GrowthSerpObservation.entity_type == "client",
            GrowthSerpObservation.observed_at >= cutoff,
        )
        .order_by(GrowthSerpObservation.observed_at.asc())
        .limit(1)
    )

    if latest_rank is None or oldest_rank is None:
        # No SERP data → neutral score (half marks)
        return _MAX_RANKING_SCORE // 2, None

    delta = latest_rank - oldest_rank  # negative = climbed up

    # Scoring:
    #   delta <= -5  (climbed 5+ positions)  → 25
    #   delta == 0   (unchanged)             → 12
    #   delta >= +5  (dropped 5+ positions)  →  0
    if delta <= -5:
        score = 25
    elif delta < 0:
        score = int(12 + (-delta) * (25 - 12) / 5)
    elif delta == 0:
        score = 12
    elif delta <= 5:
        score = int(12 - delta * 12 / 5)
    else:
        score = 0

    return max(0, min(_MAX_RANKING_SCORE, score)), delta


def _bucket(score: int) -> str:
    if score >= 80:
        return _BUCKET_UPSELL
    if score < 30:
        return _BUCKET_CHURN
    return _BUCKET_HEALTHY


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────


def compute_health_score(db: Session, user_id: UUID) -> CustomerInsight:
    """Compute (or update) the CustomerInsight row for a single user."""
    login_sc, days_inactive = _login_sub_score(db, user_id)
    resp_sc, resp_rate = _response_rate_sub_score(db, user_id)
    rank_sc, rank_delta = _ranking_sub_score(db, user_id)

    total = login_sc + resp_sc + rank_sc

    existing = db.scalar(
        select(CustomerInsight).where(CustomerInsight.user_id == user_id)
    )

    now = datetime.now(tz=timezone.utc)

    if existing:
        existing.health_score = total
        existing.bucket = _bucket(total)
        existing.login_score = login_sc
        existing.response_rate_score = resp_sc
        existing.ranking_score = rank_sc
        existing.days_since_last_activity = days_inactive
        existing.response_rate_pct = resp_rate
        existing.rank_delta = rank_delta
        existing.computed_at = now
        existing.updated_at = now
        db.commit()
        db.refresh(existing)
        return existing

    insight = CustomerInsight(
        user_id=user_id,
        health_score=total,
        bucket=_bucket(total),
        login_score=login_sc,
        response_rate_score=resp_sc,
        ranking_score=rank_sc,
        days_since_last_activity=days_inactive,
        response_rate_pct=resp_rate,
        rank_delta=rank_delta,
        computed_at=now,
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


def recompute_all_insights(db: Session) -> int:
    """Recompute health scores for all users. Returns count of users processed."""
    user_ids = db.scalars(select(User.id)).all()
    count = 0
    for uid in user_ids:
        try:
            compute_health_score(db, uid)
            count += 1
        except Exception:
            logger.exception("Failed computing health score for user %s", uid)
            db.rollback()
    return count


def record_user_session(db: Session, user_id: UUID, ip_hash: str | None = None, user_agent: str | None = None) -> None:
    """Create a UserSession row. Call from OAuth callback / auth middleware."""
    session = UserSession(
        user_id=user_id,
        ip_hash=ip_hash,
        user_agent=user_agent[:255] if user_agent else None,
    )
    db.add(session)
    db.commit()
