import uuid
from datetime import datetime, date

from sqlalchemy import JSON, Boolean, DateTime, Date, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    connection: Mapped["GoogleConnection"] = relationship(back_populates="user", uselist=False)
    lifecycle_events: Mapped[list["LifecycleEvent"]] = relationship(back_populates="user")
    churn_surveys: Mapped[list["ChurnSurvey"]] = relationship(back_populates="user")
    churn_telemetry_snapshot: Mapped["ChurnTelemetrySnapshot | None"] = relationship(back_populates="user", uselist=False)
    acknowledged_alerts: Mapped[list["ChurnAlert"]] = relationship(back_populates="acknowledged_by")
    starter_profile_settings: Mapped["StarterProfileSettings | None"] = relationship(back_populates="user", uselist=False)
    subscription_profile: Mapped["SubscriptionProfile | None"] = relationship(back_populates="user", uselist=False)
    growth_competitors: Mapped[list["GrowthCompetitor"]] = relationship(back_populates="user")
    growth_client_snapshots: Mapped[list["GrowthClientSnapshot"]] = relationship(back_populates="user")
    growth_client_service_snapshots: Mapped[list["GrowthClientServiceSnapshot"]] = relationship(back_populates="user")
    growth_client_keyword_metrics: Mapped[list["GrowthClientKeywordMetric"]] = relationship(back_populates="user")
    growth_benchmark_comparisons: Mapped[list["GrowthBenchmarkComparison"]] = relationship(back_populates="user")
    growth_sentiment_benchmark_runs: Mapped[list["GrowthSentimentBenchmarkRun"]] = relationship(back_populates="user")
    growth_sentiment_benchmark_topic_gaps: Mapped[list["GrowthSentimentBenchmarkTopicGap"]] = relationship(back_populates="user")
    growth_seo_suggestions: Mapped[list["GrowthSeoSuggestion"]] = relationship(back_populates="user")
    growth_seo_suggestion_actions: Mapped[list["GrowthSeoSuggestionAction"]] = relationship(back_populates="user")
    growth_seo_alerts: Mapped[list["GrowthSeoAlert"]] = relationship(back_populates="user")



class GoogleConnection(Base):
    __tablename__ = "google_connections"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_google_connections_user_id"),
        UniqueConstraint("location_id", name="uq_google_connections_location_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    google_account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False)
    preferred_tone: Mapped[str] = mapped_column(String(50), nullable=False, default="cercano")
    manual_approval_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    negative_review_whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="connection")
    reviews: Mapped[list["Review"]] = relationship(back_populates="connection")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("review_id", name="uq_reviews_review_id"),
        Index("ix_reviews_location_id", "location_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("google_connections.id", ondelete="CASCADE"), nullable=False)
    review_id: Mapped[str] = mapped_column(String(255), nullable=False)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False)

    rating: Mapped[int | None] = mapped_column(nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    author_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_profile_photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    author_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    author_metadata_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    raw_payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    reply_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reply_detected_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reply_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_public_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_alert_priority: Mapped[str | None] = mapped_column(String(16), nullable=True)
    reply_alert_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reply_alert_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_alert_next_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Human approval & send tracking ───────────────────────────────────────
    reply_approved_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    connection: Mapped[GoogleConnection] = relationship(back_populates="reviews")


class StarterProfileSettings(Base):
    __tablename__ = "starter_profile_settings"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_starter_profile_settings_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # CSV list entered by user. We keep raw text to preserve user intent and separators.
    forbidden_words: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Allowed values: instant | delay_1h
    response_schedule: Mapped[str] = mapped_column(String(32), nullable=False, default="instant")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="starter_profile_settings")


class SubscriptionProfile(Base):
    __tablename__ = "subscription_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_subscription_profiles_user_id"),
        Index("ix_subscription_profiles_status", "subscription_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    subscription_plan: Mapped[str] = mapped_column(String(50), nullable=False, default="starter")
    subscription_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="subscription_profile")


class StarterMonthlyMetrics(Base):
    """Pre-aggregated monthly KPIs per user / active location for Plan Starter reports.

    Populated by the reporting job using the SQL in
    backend/sql/starter_monthly_metrics_query.sql.
    Unique constraint (user_id, year, month) enforces exactly one row per
    calendar month per user so upserts are idempotent.
    """

    __tablename__ = "starter_monthly_metrics"
    __table_args__ = (
        UniqueConstraint("user_id", "year", "month", name="uq_starter_monthly_metrics_user_year_month"),
        Index("ix_starter_monthly_metrics_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[str] = mapped_column(String(128), nullable=False)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── KPI 1: volume ────────────────────────────────────────────────────────
    total_reviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── KPI 2: quality ───────────────────────────────────────────────────────
    avg_rating: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)

    # ── KPI 3: responsiveness ────────────────────────────────────────────────
    # Percentage of reviews that triggered an AUTO_REPLY (0-100).
    response_rate_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # ── KPI 4: speed ─────────────────────────────────────────────────────────
    # Average minutes from review creation to NLP decision (reply_decided_at).
    avg_response_time_minutes: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class MonthlyReport(Base):
    """Full monthly report JSON stored after the cron job runs on day 1.

    ``payload`` contains the complete structured report (KPIs + sentiment
    + chart_data) as returned by ``_build_report_payload``.  One row per
    user per calendar month; idempotent upsert used by the worker.
    """

    __tablename__ = "monthly_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "year", "month", name="uq_monthly_reports_user_year_month"),
        Index("ix_monthly_reports_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    executive_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pdf_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    pdf_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_signed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_signed_url_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# ────────────────────────────────────────────────────────────────────────────────
# CHURN & LIFECYCLE MODELS
# ────────────────────────────────────────────────────────────────────────────────


class LifecycleEvent(Base):
    """Track user journey milestones (signup, first_connection, churn_initiated, etc.)."""
    
    __tablename__ = "lifecycle_events"
    __table_args__ = (
        Index("ix_lifecycle_user_type", "user_id", "event_type"),
        Index("ix_lifecycle_created_at", "created_at"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Uses lifecycle_event_type enum
    # "metadata" is reserved by SQLAlchemy Declarative API, so map it via a safe attribute name.
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    user: Mapped[User] = relationship(back_populates="lifecycle_events")


class ChurnSurvey(Base):
    """Qualitative churn feedback - submitted by user when canceling."""
    
    __tablename__ = "churn_surveys"
    __table_args__ = (
        Index("ix_churn_survey_reason", "primary_reason"),
        Index("ix_churn_survey_date", "cancellation_date"),
        Index("ix_churn_survey_score", "satisfaction_score"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    cancellation_date: Mapped[date] = mapped_column(Date, nullable=False)
    primary_reason: Mapped[str] = mapped_column(String(50), nullable=False)  # Uses churn_reason enum
    secondary_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    satisfaction_score: Mapped[int] = mapped_column(Integer, nullable=False)
    free_text_feedback: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    would_return_if_feature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    would_return_if_price_reduction: Mapped[bool] = mapped_column(Boolean, default=False)
    reduction_amount_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    user: Mapped[User] = relationship(back_populates="churn_surveys")


class ChurnTelemetrySnapshot(Base):
    """Engagement metrics snapshot captured at churn time."""
    
    __tablename__ = "churn_telemetry_snapshot"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_telemetry_one_per_user"),
        Index("ix_telemetry_approval_rate", "approval_rate"),
        Index("ix_telemetry_active_days", "active_days_before_cancel"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    active_days_before_cancel: Mapped[int] = mapped_column(Integer, nullable=False)
    last_activity_days_ago: Mapped[int] = mapped_column(Integer, nullable=False)
    total_reviews_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_ai_responses_generated: Mapped[int] = mapped_column(Integer, default=0)
    total_ai_responses_approved: Mapped[int] = mapped_column(Integer, default=0)
    approval_rate: Mapped[float] = mapped_column(Float, nullable=False)
    used_tone_selector: Mapped[bool] = mapped_column(Boolean, default=False)
    used_sentiment_reports: Mapped[bool] = mapped_column(Boolean, default=False)
    used_manual_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    locations_connected: Mapped[int] = mapped_column(Integer, default=0)
    days_subscribed: Mapped[int] = mapped_column(Integer, default=0)
    subscription_plan: Mapped[str] = mapped_column(String(50), default="starter")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    user: Mapped[User] = relationship(back_populates="churn_telemetry_snapshot")


class ChurnAlert(Base):
    """Automated alerts triggered by churn monitoring system."""
    
    __tablename__ = "churn_alerts"
    __table_args__ = (
        Index("ix_alert_severity", "severity"),
        Index("ix_alert_triggered_at", "triggered_at"),
        Index("ix_alert_type", "alert_type"),
        Index("ix_alert_acknowledged", "acknowledged_at"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    time_window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    metric_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    alert_message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    acknowledged_by: Mapped[User | None] = relationship(back_populates="acknowledged_alerts")


# ────────────────────────────────────────────────────────────────────────────────
# GROWTH PLAN - COMPETITOR INTELLIGENCE MODELS
# ────────────────────────────────────────────────────────────────────────────────


class GrowthCompetitor(Base):
    __tablename__ = "growth_competitors"
    __table_args__ = (
        UniqueConstraint("user_id", "google_place_id", name="uq_growth_competitors_user_place"),
        Index("ix_growth_competitors_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    google_place_id: Mapped[str] = mapped_column(String(128), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="growth_competitors")
    snapshots: Mapped[list["GrowthCompetitorSnapshot"]] = relationship(back_populates="competitor")
    service_snapshots: Mapped[list["GrowthCompetitorServiceSnapshot"]] = relationship(back_populates="competitor")
    keyword_metrics: Mapped[list["GrowthCompetitorKeywordMetric"]] = relationship(back_populates="competitor")
    benchmark_comparisons: Mapped[list["GrowthBenchmarkComparison"]] = relationship(back_populates="competitor")


class GrowthClientSnapshot(Base):
    __tablename__ = "growth_client_snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "observed_at", name="uq_growth_client_snapshots_user_observed"),
        Index("ix_growth_client_snapshots_user_observed", "user_id", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    review_count_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_avg: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    posts_count_7d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    posts_count_30d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    services_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_source: Mapped[str] = mapped_column(String(60), nullable=False, default="google_maps_public")
    extraction_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="growth_client_snapshots")


class GrowthCompetitorSnapshot(Base):
    __tablename__ = "growth_competitor_snapshots"
    __table_args__ = (
        UniqueConstraint("competitor_id", "observed_at", name="uq_growth_comp_snapshots_comp_observed"),
        Index("ix_growth_competitor_snapshots_competitor_observed", "competitor_id", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_competitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    review_count_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_avg: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    posts_count_7d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    posts_count_30d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    services_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_source: Mapped[str] = mapped_column(String(60), nullable=False, default="google_maps_public")
    extraction_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    competitor: Mapped[GrowthCompetitor] = relationship(back_populates="snapshots")


class GrowthClientServiceSnapshot(Base):
    __tablename__ = "growth_client_services_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "observed_at",
            "service_name_normalized",
            name="uq_growth_client_services_user_observed_service",
        ),
        Index("ix_growth_client_services_user_observed", "user_id", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    service_name_normalized: Mapped[str] = mapped_column(String(180), nullable=False)
    service_name_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="growth_client_service_snapshots")


class GrowthCompetitorServiceSnapshot(Base):
    __tablename__ = "growth_competitor_services_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "competitor_id",
            "observed_at",
            "service_name_normalized",
            name="uq_growth_comp_services_comp_observed_service",
        ),
        Index("ix_growth_comp_services_competitor_observed", "competitor_id", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_competitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    service_name_normalized: Mapped[str] = mapped_column(String(180), nullable=False)
    service_name_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    competitor: Mapped[GrowthCompetitor] = relationship(back_populates="service_snapshots")


class GrowthClientKeywordMetric(Base):
    __tablename__ = "growth_client_keyword_metrics"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "period_start",
            "period_end",
            "keyword",
            name="uq_growth_client_keywords_user_period_keyword",
        ),
        Index("ix_growth_client_keywords_user_period", "user_id", "period_end", "mentions_count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    keyword: Mapped[str] = mapped_column(String(120), nullable=False)
    mentions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sentiment_positive_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    sentiment_neutral_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    sentiment_negative_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="growth_client_keyword_metrics")


class GrowthCompetitorKeywordMetric(Base):
    __tablename__ = "growth_competitor_keyword_metrics"
    __table_args__ = (
        UniqueConstraint(
            "competitor_id",
            "period_start",
            "period_end",
            "keyword",
            name="uq_growth_comp_keywords_comp_period_keyword",
        ),
        Index("ix_growth_comp_keywords_comp_period", "competitor_id", "period_end", "mentions_count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_competitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    keyword: Mapped[str] = mapped_column(String(120), nullable=False)
    mentions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sentiment_positive_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    sentiment_neutral_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    sentiment_negative_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    competitor: Mapped[GrowthCompetitor] = relationship(back_populates="keyword_metrics")


class GrowthBenchmarkComparison(Base):
    __tablename__ = "growth_benchmark_comparisons"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "competitor_id",
            "observed_at",
            name="uq_growth_benchmark_user_comp_observed",
        ),
        Index("ix_growth_benchmark_user_observed", "user_id", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_competitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rating_gap: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    review_count_gap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_growth_30d_gap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    posting_freq_30d_gap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    keyword_share_gap: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="growth_benchmark_comparisons")
    competitor: Mapped[GrowthCompetitor] = relationship(back_populates="benchmark_comparisons")


class GrowthSentimentBenchmarkRun(Base):
    __tablename__ = "growth_sentiment_benchmark_runs"
    __table_args__ = (
        Index("ix_growth_sentiment_benchmark_runs_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ok")
    client_sentiment_score: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    competitor_average_sentiment_score: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    client_negative_rate: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    rank_client_among_6: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    diagnostics_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="growth_sentiment_benchmark_runs")
    topic_gaps: Mapped[list["GrowthSentimentBenchmarkTopicGap"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class GrowthSentimentBenchmarkTopicGap(Base):
    __tablename__ = "growth_sentiment_benchmark_topic_gaps"
    __table_args__ = (
        Index("ix_growth_sentiment_benchmark_topic_gaps_run", "run_id"),
        Index("ix_growth_sentiment_benchmark_topic_gaps_user_label", "user_id", "label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_sentiment_benchmark_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    client_complaint_rate: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    competitor_complaint_rate: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    gap: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    support_competitors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    label: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 3), nullable=True)
    evidence_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    run: Mapped[GrowthSentimentBenchmarkRun] = relationship(back_populates="topic_gaps")
    user: Mapped[User] = relationship(back_populates="growth_sentiment_benchmark_topic_gaps")


class GrowthSeoSuggestion(Base):
    __tablename__ = "growth_seo_suggestions"
    __table_args__ = (
        Index("ix_growth_seo_suggestions_user_status", "user_id", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    suggestion_type: Mapped[str] = mapped_column(String(30), nullable=False)
    keyword: Mapped[str] = mapped_column(String(120), nullable=False)
    current_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_text: Mapped[str] = mapped_column(Text, nullable=False)
    keywords_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    justification_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, default="medio")
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="growth_seo_suggestions")
    actions: Mapped[list["GrowthSeoSuggestionAction"]] = relationship(
        back_populates="suggestion",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["GrowthSeoAlert"]] = relationship(back_populates="suggestion")


class GrowthSeoSuggestionAction(Base):
    __tablename__ = "growth_seo_suggestion_actions"
    __table_args__ = (
        Index("ix_growth_seo_suggestion_actions_suggestion_created", "suggestion_id", "created_at"),
        Index("ix_growth_seo_suggestion_actions_user_action", "user_id", "action_type", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suggestion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_seo_suggestions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ok")
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    suggestion: Mapped[GrowthSeoSuggestion] = relationship(back_populates="actions")
    user: Mapped[User] = relationship(back_populates="growth_seo_suggestion_actions")


class GrowthSeoAlert(Base):
    __tablename__ = "growth_seo_alerts"
    __table_args__ = (
        Index("ix_growth_seo_alerts_user_seen_created", "user_id", "is_seen", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    suggestion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_seo_suggestions.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(140), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(12), nullable=False, default="medium")
    is_seen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="growth_seo_alerts")
    suggestion: Mapped[GrowthSeoSuggestion | None] = relationship(back_populates="alerts")
