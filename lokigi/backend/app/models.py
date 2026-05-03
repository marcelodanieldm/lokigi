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
    growth_serp_observations: Mapped[list["GrowthSerpObservation"]] = relationship(back_populates="user")
    growth_keyword_conquest_events: Mapped[list["GrowthKeywordConquestEvent"]] = relationship(back_populates="user")
    growth_event_notifications: Mapped[list["GrowthEventNotification"]] = relationship(back_populates="user")
    competitor_entities: Mapped[list["CompetitorEntity"]] = relationship(back_populates="user")
    competitor_scrape_runs: Mapped[list["ScrapeRun"]] = relationship(back_populates="user")
    business_context_entries: Mapped[list["BusinessContext"]] = relationship(back_populates="user")
    google_qa_questions: Mapped[list["GoogleQAQuestion"]] = relationship(back_populates="user")
    competitor_history_entries: Mapped[list["CompetitorHistory"]] = relationship(back_populates="user")
    photo_optimization_jobs: Mapped[list["PhotoOptimizationJob"]] = relationship(back_populates="user")
    customer_insight: Mapped["CustomerInsight | None"] = relationship(back_populates="user", uselist=False)
    user_sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")

    # ── Auth fields ───────────────────────────────────────────────────────────
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # "email" | "google"
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False, default="email")
    # Stable Google OpenID identifier for account linking and deduplication.
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    device_verification_codes: Mapped[list["DeviceVerificationCode"]] = relationship(back_populates="user", cascade="all, delete-orphan")



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
    google_profile_description: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    pending_response: Mapped["PendingResponse | None"] = relationship(
        back_populates="review",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PendingResponse(Base):
    __tablename__ = "pending_responses"
    __table_args__ = (
        UniqueConstraint("review_pk", name="uq_pending_responses_review_pk"),
        Index("ix_pending_responses_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_pk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    tone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    review: Mapped[Review] = relationship(back_populates="pending_response")


class StarterProfileSettings(Base):
    __tablename__ = "starter_profile_settings"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_starter_profile_settings_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # CSV list entered by user. We keep raw text to preserve user intent and separators.
    forbidden_words: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Primary keywords chosen during onboarding for Growth-style radar setup.
    focus_keywords: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Google Maps place_id used for daily local ranking tracking.
    client_google_place_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
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

    # ── Usage tracking (reset monthly by a cron/startup check) ───────────────
    ai_credits_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_credits_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Free trial (Growth features for Starter users) ───────────────────────
    trial_plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BillingInvoice(Base):
    """Locally generated invoice records with WeasyPrint PDFs.
    Complements Stripe invoices for plans managed outside Stripe or for
    in-house PDF downloads.
    """

    __tablename__ = "billing_invoices"
    __table_args__ = (
        Index("ix_billing_invoices_user_id", "user_id"),
        UniqueConstraint("invoice_number", name="uq_billing_invoice_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="starter")
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    # "paid" | "pending" | "void"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class ProrationCredit(Base):
    """Records mid-cycle plan change proration calculations."""

    __tablename__ = "proration_credits"
    __table_args__ = (Index("ix_proration_credits_user_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    from_plan: Mapped[str] = mapped_column(String(50), nullable=False)
    to_plan: Mapped[str] = mapped_column(String(50), nullable=False)
    change_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    debit_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Net amount charged/credited on next invoice (positive = charge, negative = credit)
    net_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # "pending" | "applied" | "voided"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Organization(Base):
    """Multi-seat organization. One owner_user_id holds the subscription; other
    members are linked via OrgMember.  status: active | suspended | expired."""

    __tablename__ = "organizations"
    __table_args__ = (
        Index("ix_organizations_owner_user_id", "owner_user_id"),
        UniqueConstraint("slug", name="uq_organizations_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    members: Mapped[list["OrgMember"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class OrgMember(Base):
    """Links a user to an organization with a specific role.
    A row with status='invited' is created before the user accepts; user_id
    may be NULL until they register and claim the invite token.
    role hierarchy: owner > admin > member > viewer
    """

    __tablename__ = "org_members"
    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="uq_org_members_org_user"),
        Index("ix_org_members_org_id", "org_id"),
        Index("ix_org_members_user_id", "user_id"),
        Index("ix_org_members_invite_token", "invite_token"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    # NULL while invite is pending (user hasn't registered yet)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    # Invited email address (stable reference even before user_id is known)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    invite_token: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    invite_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    organization: Mapped["Organization"] = relationship(back_populates="members")


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
    photos_count_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
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
    photos_count_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
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


class GrowthSerpObservation(Base):
    __tablename__ = "growth_serp_observations"
    __table_args__ = (
        Index("ix_growth_serp_observations_user_observed", "user_id", "observed_at"),
        Index("ix_growth_serp_observations_user_keyword", "user_id", "keyword"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    competitor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_competitors.id", ondelete="SET NULL"),
        nullable=True,
    )
    keyword: Mapped[str] = mapped_column(String(120), nullable=False)
    location_label: Mapped[str] = mapped_column(String(140), nullable=False, default="default")
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False, default="client")
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="growth_serp_observations")


class GrowthKeywordConquestEvent(Base):
    __tablename__ = "growth_keyword_conquest_events"
    __table_args__ = (
        Index("ix_growth_keyword_conquest_user_conquered", "user_id", "conquered_at"),
        Index("ix_growth_keyword_conquest_user_keyword", "user_id", "keyword"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    keyword: Mapped[str] = mapped_column(String(120), nullable=False)
    location_label: Mapped[str] = mapped_column(String(140), nullable=False, default="default")
    displaced_competitor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("growth_competitors.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conquered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="growth_keyword_conquest_events")


# ────────────────────────────────────────────────────────────────────────────────
# GUERRILLA SCRAPER - ULTRA-LIGHT STORAGE MODELS
# ────────────────────────────────────────────────────────────────────────────────


class CompetitorEntity(Base):
    __tablename__ = "competitor"
    __table_args__ = (
        UniqueConstraint("user_id", "url_hash", name="uq_competitor_user_url_hash"),
        Index("ix_competitor_user_zone", "user_id", "zone_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    url_hash: Mapped[str] = mapped_column(String(40), nullable=False)
    maps_url: Mapped[str] = mapped_column(Text, nullable=False)
    name_short: Mapped[str | None] = mapped_column(String(120), nullable=True)
    zone_code: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", name="competitor_status_enum", create_type=False),
        nullable=False,
        default="active",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="competitor_entities")
    snapshots: Mapped[list["CompetitorSnapshot"]] = relationship(back_populates="competitor")
    history_entries: Mapped[list["CompetitorHistory"]] = relationship(back_populates="competitor")


class ScrapeRun(Base):
    __tablename__ = "scrape_run"
    __table_args__ = (
        Index("ix_scrape_run_user_started", "user_id", "started_at"),
        Index("ix_scrape_run_status", "status", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("running", "ok", "partial", "error", "blocked", name="scrape_status_enum", create_type=False),
        nullable=False,
        default="running",
    )
    total_targets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="competitor_scrape_runs")
    snapshots: Mapped[list["CompetitorSnapshot"]] = relationship(back_populates="scrape_run")


class CompetitorSnapshot(Base):
    __tablename__ = "competitor_snapshot"
    __table_args__ = (
        UniqueConstraint("scrape_run_id", "competitor_id", name="uq_comp_snapshot_run_competitor"),
        Index("ix_comp_snapshot_competitor_date", "competitor_id", "observed_on"),
        Index("ix_comp_snapshot_status", "source_status", "observed_on"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scrape_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scrape_run.id", ondelete="CASCADE"),
        nullable=False,
    )
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competitor.id", ondelete="CASCADE"),
        nullable=False,
    )
    observed_on: Mapped[date] = mapped_column(Date, nullable=False)
    rating_x100: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_reviews: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_bucket: Mapped[str] = mapped_column(
        Enum("unknown", "budget", "mid", "premium", "luxury", name="price_bucket_enum", create_type=False),
        nullable=False,
        default="unknown",
    )
    category_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    address_hash: Mapped[str | None] = mapped_column(String(40), nullable=True)
    posts_30d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_status: Mapped[str] = mapped_column(
        Enum("ok", "partial", "error", "blocked", name="scrape_status_enum", create_type=False),
        nullable=False,
        default="ok",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    scrape_run: Mapped[ScrapeRun] = relationship(back_populates="snapshots")
    competitor: Mapped[CompetitorEntity] = relationship(back_populates="snapshots")
    services: Mapped[list["CompetitorServiceMap"]] = relationship(back_populates="snapshot")


class ServiceCatalog(Base):
    __tablename__ = "service_catalog"
    __table_args__ = (
        UniqueConstraint("code", name="uq_service_catalog_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    label_short: Mapped[str] = mapped_column(String(80), nullable=False)

    snapshot_links: Mapped[list["CompetitorServiceMap"]] = relationship(back_populates="service")


class CompetitorServiceMap(Base):
    __tablename__ = "competitor_service_map"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "service_id", name="uq_comp_service_map_snapshot_service"),
        Index("ix_comp_service_map_service", "service_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competitor_snapshot.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("service_catalog.id", ondelete="CASCADE"),
        nullable=False,
    )
    present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    snapshot: Mapped[CompetitorSnapshot] = relationship(back_populates="services")
    service: Mapped[ServiceCatalog] = relationship(back_populates="snapshot_links")


class GrowthEventNotification(Base):
    __tablename__ = "growth_event_notifications"
    __table_args__ = (
        Index("ix_growth_event_notifications_user_created", "user_id", "created_at"),
        Index("ix_growth_event_notifications_status_created", "status", "created_at"),
        Index("ix_growth_event_notifications_dedupe_created", "dedupe_key", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(12), nullable=False, default="medium")
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    report_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    send_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_seen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="growth_event_notifications")


# ────────────────────────────────────────────────────────────────────────────────
# GOOGLE Q&A MANAGER - FAQ AUTOMATION MODELS
# ────────────────────────────────────────────────────────────────────────────────


class BusinessContext(Base):
    """Structured knowledge base for a business location.

    Stores menu items, description snippets and pre-loaded FAQ pairs.
    The RAG engine uses these entries to auto-answer Google Q&A questions.

    context_type values:
      - 'menu'        : free-text block describing products/services
      - 'description' : copied from GBP profile description
      - 'faq'         : a user-defined question + answer pair
    """

    __tablename__ = "business_context"
    __table_args__ = (
        Index("ix_business_context_user_type", "user_id", "context_type"),
        Index("ix_business_context_active", "user_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[str] = mapped_column(String(128), nullable=False)
    context_type: Mapped[str] = mapped_column(String(20), nullable=False)  # menu | description | faq
    # For faq entries: the question text the user pre-loaded
    faq_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Main content: answer for faq, free text for menu/description
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="business_context_entries")


class GoogleQAQuestion(Base):
    """Tracks questions detected via the Google Business Profile Q&A API.

    status values:
      - 'pending'          : new question, not yet processed
      - 'auto_answered'    : RAG engine answered with confidence >= 80%
      - 'needs_intervention': RAG confidence < 80% or no match found
      - 'user_answered'    : the business owner answered manually via Lokigi
      - 'ignored'          : user dismissed the question
    """

    __tablename__ = "google_qa_questions"
    __table_args__ = (
        UniqueConstraint("google_question_id", name="uq_google_qa_question_id"),
        Index("ix_google_qa_user_status", "user_id", "status"),
        Index("ix_google_qa_user_detected", "user_id", "detected_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[str] = mapped_column(String(128), nullable=False)
    # Resource name from Google API e.g. "locations/12345/questions/67890"
    google_question_id: Mapped[str] = mapped_column(String(255), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    author_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    upvote_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # RAG engine output
    auto_answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)  # 0-100
    matched_context_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    status: Mapped[str] = mapped_column(String(25), nullable=False, default="pending")
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Final text actually sent to Google (could be edited by user)
    sent_answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="google_qa_questions")


# ────────────────────────────────────────────────────────────────────────────────
# LOCAL SCOUT — COMPETITOR HISTORY (48h Playwright scrape)
# ────────────────────────────────────────────────────────────────────────────────


class CompetitorHistory(Base):
    """Time-series snapshot produced every 48 h by the Local Scout Celery task.

    Each row captures the publicly visible metrics for one competitor URL at
    one point in time.  Backed by the ``competitor_history`` table.
    """

    __tablename__ = "competitor_history"
    __table_args__ = (
        Index("ix_competitor_history_user_scraped", "user_id", "scraped_at"),
        Index("ix_competitor_history_competitor_scraped", "competitor_id", "scraped_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    competitor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("competitor.id", ondelete="CASCADE"),
        nullable=False,
    )
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rating_avg: Mapped[float | None] = mapped_column(Float, nullable=True)        # 0.0 – 5.0
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_post_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    scrape_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ok"
    )  # ok | partial | error | blocked

    competitor: Mapped["CompetitorEntity"] = relationship(back_populates="history_entries")
    user: Mapped["User"] = relationship(back_populates="competitor_history_entries")


# ────────────────────────────────────────────────────────────────────────────────
# PHOTO OPTIMIZER — JOB LOG
# ────────────────────────────────────────────────────────────────────────────────


class PhotoOptimizationJob(Base):
    """Audit log for every Smart-Upload processed via /photo/optimize.

    One row per upload.  Stores the checklist outcome and the generated alt-text
    so users can copy it without re-processing.
    """

    __tablename__ = "photo_optimization_jobs"
    __table_args__ = (
        Index("ix_photo_jobs_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gps_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_injected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    alt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    alt_text_source: Mapped[str | None] = mapped_column(String(32), nullable=True)  # llm | keyword
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="photo_optimization_jobs")


# ────────────────────────────────────────────────────────────────────────────────
# CRM — CUSTOMER INSIGHT  (Health Score + CEO notes)
# ────────────────────────────────────────────────────────────────────────────────


class CustomerInsight(Base):
    """Computed Customer Health Score and CEO annotations per user.

    Health Score 0-100 derived from:
      • login_score        (0-40)  — platform activity recency
      • response_rate_score(0-35)  — % of reviews with reply_sent_at
      • ranking_score      (0-25)  — SERP rank improvement vs 30 days ago

    Buckets:
      score >= 80  → upsell_candidate
      score <  30  → churn_risk
      else         → healthy
    """

    __tablename__ = "customer_insights"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_customer_insights_user_id"),
        Index("ix_customer_insights_score", "health_score"),
        Index("ix_customer_insights_bucket", "bucket"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    health_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bucket: Mapped[str] = mapped_column(
        String(32), nullable=False, default="healthy"
    )  # upsell_candidate | healthy | churn_risk

    # Component sub-scores stored for transparency
    login_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_rate_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ranking_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Raw metrics stored alongside scores
    days_since_last_activity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_rate_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    rank_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)  # negative = improved

    # CEO annotations
    ceo_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="customer_insight")


# ────────────────────────────────────────────────────────────────────────────────
# CRM — USER SESSION  (lightweight login tracker)
# ────────────────────────────────────────────────────────────────────────────────


class UserSession(Base):
    """One row per platform login / OAuth token validation.

    Created by the auth middleware / OAuth callback to track login frequency.
    Only id, user_id and created_at are required — ip_hash is optional and
    stored as a SHA-256 hex to avoid storing raw IPs.
    """

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="user_sessions")


# ────────────────────────────────────────────────────────────────────────────────
# OKR MONITOR — Objetivos y Resultados Clave
# ────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────
# AUTH — Enterprise config, password reset, device verification
# ────────────────────────────────────────────────────────────────────────────────


class EnterpriseConfig(Base):
    """White-label branding config for an Enterprise org.
    Controls the login screen appearance at /login/enterprise/{slug}.
    """

    __tablename__ = "enterprise_configs"
    __table_args__ = (
        UniqueConstraint("org_id", name="uq_enterprise_configs_org_id"),
        Index("ix_enterprise_configs_login_domain", "login_domain"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    brand_primary_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6366f1")
    brand_bg_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#f8fafc")
    welcome_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Custom domain, e.g. "login.myagency.com"
    login_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    mfa_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_password_length: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class PasswordResetToken(Base):
    """Single-use password reset token (1-hour TTL)."""

    __tablename__ = "password_reset_tokens"
    __table_args__ = (Index("ix_prt_user_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="password_reset_tokens")


class DeviceVerificationCode(Base):
    """6-digit OTP sent by email when a suspicious IP is detected (10-minute TTL)."""

    __tablename__ = "device_verification_codes"
    __table_args__ = (Index("ix_dvc_user_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # SHA-256 of the 6-digit code — never store plaintext
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="device_verification_codes")

class OKRObjective(Base):
    """A single quarterly objective (company-level — no user FK).

    Examples
    --------
    "Alcanzar masa crítica de locales Enterprise"
    "Reducir el Churn Rate por debajo del 3 %"
    """

    __tablename__ = "okr_objectives"
    __table_args__ = (
        Index("ix_okr_objectives_quarter_year", "quarter", "year"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-4
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(64), nullable=True)  # CEO | Product | Sales
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    key_results: Mapped[list["OKRKeyResult"]] = relationship(
        back_populates="objective",
        cascade="all, delete-orphan",
        order_by="OKRKeyResult.sort_order",
    )


class OKRKeyResult(Base):
    """One measurable Key Result within an Objective.

    metric_source links to an auto-computed value; current_value_override
    is used when metric_source is None or 'manual'.

    direction:
        'increase' — higher current_value = more progress  (default)
        'decrease' — lower current_value = more progress   (e.g. churn rate)
    """

    __tablename__ = "okr_key_results"
    __table_args__ = (
        Index("ix_okr_kr_objective_id", "objective_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objective_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("okr_objectives.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="")  # locales, %, $, usuarios…

    # Target and baseline
    target_value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    baseline_value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)

    # Auto-computed metric key (see okr_service.METRIC_RESOLVERS)
    # Allowed values: count_users | count_active_subscriptions | count_enterprise_plans |
    #   count_growth_plans | count_starter_plans | count_google_connections |
    #   count_reviews_total | count_reviews_replied | avg_response_rate_pct |
    #   count_upsell_candidates | count_churn_risk | count_lifecycle_churn_quarter |
    #   count_monthly_reports | manual
    metric_source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")

    # Manual override — used when metric_source is 'manual'
    current_value_override: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)

    # 'increase' or 'decrease'
    direction: Mapped[str] = mapped_column(String(16), nullable=False, default="increase")

    weight: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=1.0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    objective: Mapped["OKRObjective"] = relationship(back_populates="key_results")

