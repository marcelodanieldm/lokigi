"""Churn correlation analysis and reporting.

Analyzes relationships between churn reasons and engagement metrics,
generates insights for product team decisions.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import UUID

from app.models import ChurnSurvey, ChurnTelemetrySnapshot, Review
from app.telemetry_models import (
    ChurnReasonOption,
    ChurnCorrelationAnalysis,
)


async def analyze_churn_correlation(
    db: Session,
    time_window_days: int = 30,
) -> ChurnCorrelationAnalysis:
    """
    Deep-dive analysis of churn reasons vs engagement metrics.
    
    For each churn reason, calculate:
    - Count of churners citing that reason
    - Average active days before churn
    - Average approval rate
    - Average AI responses approved
    - % who used tone selector
    - % with low engagement (<50% approval, <7 days)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
    cutoff_date_only = cutoff_date.date()
    
    analysis_date = datetime.utcnow()
    
    correlations = []
    
    # Analyze each churn reason
    for reason in ChurnReasonOption:
        # Churners with this reason
        reason_churns_subquery = (
            select(ChurnSurvey.user_id)
            .where(
                ChurnSurvey.cancellation_date >= cutoff_date_only,
                ChurnSurvey.primary_reason == reason.value,
            )
        )
        
        # Count for this reason
        total_with_reason = db.scalar(
            select(func.count())
            .select_from(ChurnSurvey)
            .where(
                ChurnSurvey.cancellation_date >= cutoff_date_only,
                ChurnSurvey.primary_reason == reason.value,
            )
        ) or 0
        
        if total_with_reason == 0:
            continue
        
        # Total churn in window
        total_all_churn = db.scalar(
            select(func.count(ChurnSurvey.id))
            .where(ChurnSurvey.cancellation_date >= cutoff_date_only)
        ) or 1
        
        # Metrics for churners with this reason
        metrics = db.execute(
            select(
                func.avg(ChurnTelemetrySnapshot.active_days_before_cancel),
                func.avg(ChurnTelemetrySnapshot.approval_rate),
                func.avg(ChurnTelemetrySnapshot.total_ai_responses_approved),
                func.sum(
                    func.cast(
                        ChurnTelemetrySnapshot.used_tone_selector,
                        type_=func.integer
                    )
                ),
                func.count(ChurnTelemetrySnapshot.id),
            )
            .join(ChurnSurvey, ChurnSurvey.user_id == ChurnTelemetrySnapshot.user_id)
            .where(
                ChurnSurvey.cancellation_date >= cutoff_date_only,
                ChurnSurvey.primary_reason == reason.value,
            )
        ).first()
        
        avg_active_days = metrics[0] if metrics[0] else 0
        avg_approval_rate = metrics[1] if metrics[1] else 0
        avg_responses_approved = metrics[2] if metrics[2] else 0
        tone_selector_count = metrics[3] or 0
        telemetry_count = metrics[4] or 1
        
        pct_used_tone = (tone_selector_count / telemetry_count * 100) if telemetry_count > 0 else 0
        
        # Low engagement: approval < 50%, active_days < 7
        low_engagement_count = db.scalar(
            select(func.count(ChurnTelemetrySnapshot.id))
            .join(ChurnSurvey, ChurnSurvey.user_id == ChurnTelemetrySnapshot.user_id)
            .where(
                ChurnSurvey.cancellation_date >= cutoff_date_only,
                ChurnSurvey.primary_reason == reason.value,
                ChurnTelemetrySnapshot.approval_rate < 0.5,
                ChurnTelemetrySnapshot.active_days_before_cancel < 7,
            )
        ) or 0
        
        pct_low_engagement = (low_engagement_count / total_with_reason * 100) if total_with_reason > 0 else 0
        
        correlation = ChurnCorrelationAnalysis.ReasonCorrelation(
            reason=reason.value,
            churn_count=total_with_reason,
            pct_of_total=(total_with_reason / total_all_churn * 100),
            avg_active_days=round(avg_active_days, 1),
            avg_approval_rate=round(avg_approval_rate, 3),
            avg_responses_approved=round(avg_responses_approved, 1),
            pct_used_tone_selector=round(pct_used_tone, 1),
            pct_low_engagement=round(pct_low_engagement, 1),
        )
        correlations.append(correlation)
    
    # Sort by churn count (descending)
    correlations.sort(key=lambda x: x.churn_count, reverse=True)
    
    # Generate key insights
    insights = []
    
    if correlations:
        top_reason = correlations[0]
        insights.append(
            f"Top churn reason: {top_reason.reason} ({top_reason.churn_count} churns, "
            f"{top_reason.pct_of_total:.1f}% of total)"
        )
        
        # Check for low engagement pattern
        low_eng_reasons = [c for c in correlations if c.pct_low_engagement > 40]
        if low_eng_reasons:
            insight = f"High low-engagement churn: {', '.join([r.reason for r in low_eng_reasons])} "
            insight += "(users didn't fully adopt before leaving)"
            insights.append(insight)
        
        # Check for tone selector adoption among churners
        tone_adopted = [c for c in correlations if c.pct_used_tone_selector > 50]
        if tone_adopted:
            insight = f"Tone selector used: {', '.join([r.reason for r in tone_adopted])} "
            insight += "(feature adoption not preventing churn)"
            insights.append(insight)
        else:
            insights.append("Tone selector underutilized among churners - improve onboarding")
        
        # Price sensitivity check
        price_reason = next((c for c in correlations if c.reason == "price_too_high"), None)
        if price_reason and price_reason.pct_of_total > 25:
            insights.append(
                f"Price sensitivity: {price_reason.pct_of_total:.1f}% of churn - "
                f"Consider tiered pricing or discount strategy"
            )
    
    return ChurnCorrelationAnalysis(
        analysis_date=analysis_date,
        time_window_days=time_window_days,
        correlations=correlations,
        key_insights=insights[:5],  # Top 5 insights
    )


async def get_churn_cohort_analysis(
    db: Session,
    time_window_days: int = 90,
) -> dict:
    """
    Cohort analysis: Group churners by signup cohort, track churn rates over time.
    
    Useful for identifying if churn is concentrated in certain cohorts
    (e.g., recent signups vs established users).
    """
    cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
    
    # Get cohorts (group by signup month)
    cohort_data = db.execute(
        select(
            func.date_trunc('month', ChurnSurvey.created_at),
            func.count(ChurnSurvey.id),
            func.avg(ChurnTelemetrySnapshot.active_days_before_cancel),
            func.avg(ChurnTelemetrySnapshot.approval_rate),
        )
        .join(ChurnTelemetrySnapshot, ChurnSurvey.user_id == ChurnTelemetrySnapshot.user_id)
        .where(ChurnSurvey.created_at >= cutoff_date)
        .group_by(func.date_trunc('month', ChurnSurvey.created_at))
        .order_by(func.date_trunc('month', ChurnSurvey.created_at))
    ).all()
    
    cohorts = []
    for month, count, avg_active_days, avg_approval in cohort_data:
        cohorts.append({
            "month": month.strftime("%Y-%m") if month else None,
            "churns": count,
            "avg_active_days": round(avg_active_days or 0, 1),
            "avg_approval_rate": round(avg_approval or 0, 3),
        })
    
    return {
        "time_window_days": time_window_days,
        "cohorts": cohorts,
        "total_churns": sum(c["churns"] for c in cohorts),
    }
