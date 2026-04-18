"""Telemetry models for churn tracking and lifecycle events.

Pydantic schemas for validating churn survey submissions,
engagement metrics, and alert generation.
"""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class ChurnReasonOption(str, Enum):
    """Primary reasons for churn - must align with DB enum."""
    PRICE_TOO_HIGH = "price_too_high"
    LACK_OF_FEATURES = "lack_of_features"
    EASE_OF_USE_DIFFICULTY = "ease_of_use_difficulty"
    SWITCHED_COMPETITOR = "switched_competitor"
    NOT_USING_ENOUGH = "not_using_enough"
    POOR_SUPPORT = "poor_support"
    TECHNICAL_ISSUES = "technical_issues"
    PERSONAL_REASONS = "personal_reasons"
    OTHER = "other"


class LifecycleEventType(str, Enum):
    """Key events in user lifecycle."""
    SIGNUP = "signup"
    FIRST_CONNECTION = "first_connection"
    FIRST_REPLY_GENERATED = "first_reply_generated"
    FIRST_REPLY_APPROVED = "first_reply_approved"
    ONBOARDING_COMPLETE = "onboarding_complete"
    PAYMENT_METHOD_ADDED = "payment_method_added"
    SUBSCRIPTION_ACTIVATED = "subscription_activated"
    SUBSCRIPTION_DOWNGRADE = "subscription_downgrade"
    SUBSCRIPTION_PAUSED = "subscription_paused"
    CHURN_INITIATED = "churn_initiated"


class ChurnSurveyPayload(BaseModel):
    """User churn feedback submission."""
    
    user_id: UUID = Field(..., description="User submitting churn feedback")
    primary_reason: ChurnReasonOption = Field(..., description="Main reason for cancellation")
    secondary_reasons: list[ChurnReasonOption] = Field(
        default_factory=list,
        description="Additional reasons (optional)"
    )
    satisfaction_score: int = Field(
        ...,
        ge=1,
        le=5,
        description="1-5 satisfaction rating"
    )
    free_text_feedback: str | None = Field(
        default=None,
        max_length=1000,
        description="Open feedback from user"
    )
    would_return_if_feature: str | None = Field(
        default=None,
        max_length=255,
        description="Feature that would make them return"
    )
    would_return_if_price_reduction: bool = Field(
        default=False,
        description="Would user stay with price reduction?"
    )
    reduction_amount_percent: int | None = Field(
        default=None,
        ge=5,
        le=50,
        description="Suggested discount percentage"
    )


class ChurnTelemetrySnapshot(BaseModel):
    """Engagement metrics captured at churn time."""
    
    user_id: UUID
    active_days_before_cancel: int = Field(..., description="Days between first and last activity")
    last_activity_days_ago: int = Field(..., description="Days since last activity")
    total_reviews_processed: int = Field(..., ge=0)
    total_ai_responses_generated: int = Field(..., ge=0)
    total_ai_responses_approved: int = Field(..., ge=0)
    approval_rate: float = Field(..., ge=0.0, le=1.0, description="Approval % as decimal (0.0-1.0)")
    used_tone_selector: bool = Field(default=False)
    used_sentiment_reports: bool = Field(default=False)
    used_manual_approval: bool = Field(default=False)
    locations_connected: int = Field(..., ge=0)
    days_subscribed: int = Field(..., ge=0)
    subscription_plan: str = Field(default="starter")


class LifecycleEventPayload(BaseModel):
    """Log a user lifecycle event."""
    
    user_id: UUID
    event_type: LifecycleEventType
    metadata: dict | None = Field(default=None, description="Additional context")


class ChurnAlertResponse(BaseModel):
    """Alert triggered by churn monitoring system."""
    
    id: str
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    triggered_at: datetime
    time_window_days: int
    metric_name: str | None
    metric_value: float | None
    threshold_value: float | None
    details: dict | None
    acknowledged: bool


class ChurnAnalyticsResponse(BaseModel):
    """Dashboard response for churn analytics."""
    
    period_days: int
    total_churn: int
    
    class ChurnReasonBreakdown(BaseModel):
        reason: str
        count: int
        pct: float
        alert_threshold_exceeded: bool
    
    churn_by_reason: list[ChurnReasonBreakdown]
    
    class SatisfactionData(BaseModel):
        reason: str
        avg_score: float | None
        respondents: int
    
    satisfaction_by_reason: list[SatisfactionData]
    
    class PriceSensitivity(BaseModel):
        count_would_return: int
        pct_of_churn: float
    
    price_sensitivity: PriceSensitivity
    recent_alerts: list[ChurnAlertResponse]


class ChurnCorrelationAnalysis(BaseModel):
    """Deep-dive correlation between churn reason and engagement metrics."""
    
    class ReasonCorrelation(BaseModel):
        reason: str
        churn_count: int
        pct_of_total: float
        avg_active_days: float
        avg_approval_rate: float
        avg_responses_approved: float
        pct_used_tone_selector: float
        pct_low_engagement: float
    
    analysis_date: datetime
    time_window_days: int
    correlations: list[ReasonCorrelation]
    key_insights: list[str]
