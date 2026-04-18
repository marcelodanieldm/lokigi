"""Churn alert engine for automated monitoring and alerting.

Monitors churn patterns and triggers alerts for:
- High ease-of-use difficulty churn (>20%)
- Unexpected churn rate spikes
- Low engagement churn patterns
- Price sensitivity trends
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from uuid import UUID

from app.models import ChurnSurvey, ChurnTelemetrySnapshot, ChurnAlert, User, Review, GoogleConnection
from app.telemetry_models import ChurnReasonOption


async def check_ease_of_use_churn_spike(
    db: Session,
    time_window_days: int = 30,
) -> ChurnAlert | None:
    """
    Alert if >20% of churners cite 'Ease of Use Difficulty' in last N days.
    
    This is the PRIMARY alert for the Product team - indicates UX/onboarding issues.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
    cutoff_date_only = cutoff_date.date()
    
    # Total churn in window
    total_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(ChurnSurvey.cancellation_date >= cutoff_date_only)
    ) or 0
    
    if total_churn < 5:  # Minimum for statistical significance
        return None
    
    # Churn attributed to ease of use difficulty
    difficulty_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(
            ChurnSurvey.cancellation_date >= cutoff_date_only,
            ChurnSurvey.primary_reason == ChurnReasonOption.EASE_OF_USE_DIFFICULTY.value,
        )
    ) or 0
    
    pct_difficulty = (difficulty_churn / total_churn * 100) if total_churn > 0 else 0
    
    # Alert threshold: 20%
    if pct_difficulty > 20:
        alert = ChurnAlert(
            alert_type="high_churn_difficulty",
            severity="HIGH",
            triggered_at=datetime.utcnow(),
            time_window_days=time_window_days,
            metric_name="churn_difficulty_pct",
            metric_value=pct_difficulty,
            threshold_value=20.0,
            alert_message=(
                f"⚠️ HIGH ALERT: {pct_difficulty:.1f}% of churn ({difficulty_churn}/{total_churn}) "
                f"attributed to 'Ease of Use Difficulty' in last {time_window_days} days.\n\n"
                f"RECOMMENDED ACTIONS:\n"
                f"1. UX Audit - Review onboarding flow and dashboard navigation\n"
                f"2. Documentation - Improve getting-started guides and tutorials\n"
                f"3. Product - Identify pain points from free-text feedback\n"
                f"4. Support - Increase proactive outreach to new users"
            ),
            details={
                "churn_count_total": total_churn,
                "churn_count_difficulty": difficulty_churn,
                "percentage": round(pct_difficulty, 2),
                "time_window_days": time_window_days,
            }
        )
        db.add(alert)
        db.commit()
        return alert
    
    return None


async def check_churn_rate_spike(
    db: Session,
    baseline_days: int = 60,
    recent_days: int = 7,
) -> ChurnAlert | None:
    """
    Alert if recent churn rate exceeds baseline by >50%.
    
    Indicates sudden change in product satisfaction or external event.
    """
    baseline_start = (datetime.utcnow() - timedelta(days=baseline_days + recent_days)).date()
    baseline_end = (datetime.utcnow() - timedelta(days=recent_days)).date()
    recent_start = (datetime.utcnow() - timedelta(days=recent_days)).date()
    
    # Baseline: signups and churns in baseline period
    baseline_signups = db.scalar(
        select(func.count(User.id))
        .where(
            User.created_at >= baseline_start,
            User.created_at < baseline_end,
        )
    ) or 1
    
    baseline_churns = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(
            ChurnSurvey.cancellation_date >= baseline_start,
            ChurnSurvey.cancellation_date < baseline_end,
        )
    ) or 0
    
    baseline_rate = (baseline_churns / baseline_signups * 100) if baseline_signups > 0 else 0
    
    # Recent: signups and churns in recent period
    recent_signups = db.scalar(
        select(func.count(User.id))
        .where(User.created_at >= recent_start)
    ) or 1
    
    recent_churns = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(ChurnSurvey.cancellation_date >= recent_start)
    ) or 0
    
    recent_rate = (recent_churns / recent_signups * 100) if recent_signups > 0 else 0
    
    # Alert if spike >50% and absolute rate >5%
    spike_threshold = baseline_rate * 1.5
    
    if recent_rate > spike_threshold and recent_rate > 5:
        spike_increase_pct = ((recent_rate / baseline_rate) - 1) * 100 if baseline_rate > 0 else 0
        
        alert = ChurnAlert(
            alert_type="spike_in_churn_rate",
            severity="CRITICAL",
            triggered_at=datetime.utcnow(),
            time_window_days=recent_days,
            metric_name="churn_rate_pct",
            metric_value=recent_rate,
            threshold_value=spike_threshold,
            alert_message=(
                f"🚨 CRITICAL: Churn rate spiked to {recent_rate:.1f}% "
                f"(baseline: {baseline_rate:.1f}%, +{spike_increase_pct:.0f}%) "
                f"in last {recent_days} days ({recent_churns} churns from {recent_signups} signups).\n\n"
                f"IMMEDIATE ACTION REQUIRED:\n"
                f"1. Investigate recent changes - deploy, pricing, features\n"
                f"2. Check churn survey feedback for common themes\n"
                f"3. Review system logs for errors or downtime\n"
                f"4. Contact top-churn users for quick feedback"
            ),
            details={
                "baseline_rate": round(baseline_rate, 2),
                "recent_rate": round(recent_rate, 2),
                "spike_increase_pct": round(spike_increase_pct, 1),
                "baseline_period_days": baseline_days,
                "recent_period_days": recent_days,
                "recent_churns": recent_churns,
                "recent_signups": recent_signups,
            }
        )
        db.add(alert)
        db.commit()
        return alert
    
    return None


async def check_low_engagement_churn_pattern(
    db: Session,
    time_window_days: int = 30,
) -> ChurnAlert | None:
    """
    Alert if high % of churners have low engagement metrics.
    
    Indicates users are leaving without fully trying the product.
    Suggests onboarding/first-use experience issues.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
    cutoff_date_only = cutoff_date.date()
    
    # Total churn
    total_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(ChurnSurvey.cancellation_date >= cutoff_date_only)
    ) or 0
    
    if total_churn == 0:
        return None
    
    # Low engagement churners: approval_rate < 50%, active_days < 7
    low_engagement_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .join(
            ChurnTelemetrySnapshot,
            ChurnSurvey.user_id == ChurnTelemetrySnapshot.user_id,
        )
        .where(
            ChurnSurvey.cancellation_date >= cutoff_date_only,
            ChurnTelemetrySnapshot.approval_rate < 0.5,
            ChurnTelemetrySnapshot.active_days_before_cancel < 7,
        )
    ) or 0
    
    pct_low_engagement = (low_engagement_churn / total_churn * 100) if total_churn > 0 else 0
    
    # Alert threshold: 40%
    if pct_low_engagement > 40:
        alert = ChurnAlert(
            alert_type="low_engagement_churn",
            severity="MEDIUM",
            triggered_at=datetime.utcnow(),
            time_window_days=time_window_days,
            metric_name="low_engagement_churn_pct",
            metric_value=pct_low_engagement,
            threshold_value=40.0,
            alert_message=(
                f"⚠️ {pct_low_engagement:.1f}% of recent churn ({low_engagement_churn}/{total_churn}) "
                f"comes from low-engagement users (<50% approval, <7 active days).\n\n"
                f"These users didn't fully adopt the product. Focus areas:\n"
                f"1. ONBOARDING - Simplify first-use experience\n"
                f"2. QUICK WINS - Show value faster (first reply in <3 min)\n"
                f"3. ENGAGEMENT - Email/in-app nudges for inactive users\n"
                f"4. DOCS - Make getting-started more discoverable"
            ),
            details={
                "low_engagement_churn_count": low_engagement_churn,
                "total_churn_count": total_churn,
                "percentage": round(pct_low_engagement, 2),
                "threshold_days_active": 7,
                "threshold_approval_rate": 0.5,
            }
        )
        db.add(alert)
        db.commit()
        return alert
    
    return None


async def check_price_sensitivity_spike(
    db: Session,
    time_window_days: int = 30,
) -> ChurnAlert | None:
    """
    Alert if >25% of churners would stay with price reduction OR
    >30% cite price as primary reason.
    
    Indicates pricing may be barrier to adoption.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
    cutoff_date_only = cutoff_date.date()
    
    total_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(ChurnSurvey.cancellation_date >= cutoff_date_only)
    ) or 0
    
    if total_churn < 5:
        return None
    
    # Count: would return with discount
    would_return_with_discount = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(
            ChurnSurvey.cancellation_date >= cutoff_date_only,
            ChurnSurvey.would_return_if_price_reduction == True,
        )
    ) or 0
    
    # Count: primary reason is price
    price_reason_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(
            ChurnSurvey.cancellation_date >= cutoff_date_only,
            ChurnSurvey.primary_reason == ChurnReasonOption.PRICE_TOO_HIGH.value,
        )
    ) or 0
    
    pct_would_return = (would_return_with_discount / total_churn * 100) if total_churn > 0 else 0
    pct_price_reason = (price_reason_churn / total_churn * 100) if total_churn > 0 else 0
    
    # Alert if either threshold exceeded
    if pct_would_return > 25 or pct_price_reason > 30:
        alert = ChurnAlert(
            alert_type="high_churn_price_sensitivity",
            severity="MEDIUM",
            triggered_at=datetime.utcnow(),
            time_window_days=time_window_days,
            metric_name="price_sensitivity_pct",
            metric_value=max(pct_would_return, pct_price_reason),
            threshold_value=max(25.0, 30.0),
            alert_message=(
                f"💰 Price sensitivity detected: {pct_would_return:.1f}% would return with discount, "
                f"{pct_price_reason:.1f}% cite price as reason.\n\n"
                f"PRICING STRATEGY OPTIONS:\n"
                f"1. Discount tiers for long-term contracts\n"
                f"2. Freemium model (limited free tier)\n"
                f"3. Per-location pricing (currently per-business)\n"
                f"4. Money-back guarantee (reduce purchase anxiety)\n"
                f"5. Value communication - highlight ROI metrics"
            ),
            details={
                "would_return_pct": round(pct_would_return, 2),
                "price_reason_pct": round(pct_price_reason, 2),
                "would_return_count": would_return_with_discount,
                "price_reason_count": price_reason_churn,
                "total_churn_count": total_churn,
            }
        )
        db.add(alert)
        db.commit()
        return alert
    
    return None


async def run_all_churn_checks(db: Session) -> list[ChurnAlert]:
    """
    Run all churn monitoring checks and return triggered alerts.
    
    Typically called daily by APScheduler job.
    """
    alerts = []
    
    # Main alert: ease of use difficulty
    alert = await check_ease_of_use_churn_spike(db, time_window_days=30)
    if alert:
        alerts.append(alert)
    
    # Critical: churn rate spike
    alert = await check_churn_rate_spike(db, baseline_days=60, recent_days=7)
    if alert:
        alerts.append(alert)
    
    # Important: low engagement churn
    alert = await check_low_engagement_churn_pattern(db, time_window_days=30)
    if alert:
        alerts.append(alert)
    
    # Business: price sensitivity
    alert = await check_price_sensitivity_spike(db, time_window_days=30)
    if alert:
        alerts.append(alert)
    
    return alerts
