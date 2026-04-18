import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    connection: Mapped["GoogleConnection"] = relationship(back_populates="user", uselist=False)


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
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
