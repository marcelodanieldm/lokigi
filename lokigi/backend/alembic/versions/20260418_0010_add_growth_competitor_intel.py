"""add growth competitor intelligence tables

Revision ID: 20260418_0010
Revises: 20260418_0009
Create Date: 2026-04-18 22:10:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision: str = "20260418_0010"
down_revision: Union[str, None] = "20260418_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Competitors defined per client (user) for Growth benchmark.
    op.create_table(
        "growth_competitors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("google_place_id", sa.String(length=128), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "google_place_id", name="uq_growth_competitors_user_place"),
    )
    op.create_index("ix_growth_competitors_user_id", "growth_competitors", ["user_id"])

    # Snapshot of the client's own public profile metrics to compare against competitors.
    op.create_table(
        "growth_client_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_count_total", sa.Integer(), nullable=True),
        sa.Column("rating_avg", sa.Numeric(4, 2), nullable=True),
        sa.Column("posts_count_7d", sa.Integer(), nullable=True),
        sa.Column("posts_count_30d", sa.Integer(), nullable=True),
        sa.Column("services_count", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(length=60), nullable=False, server_default="google_maps_public"),
        sa.Column("extraction_job_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "observed_at", name="uq_growth_client_snapshots_user_observed"),
    )
    op.create_index(
        "ix_growth_client_snapshots_user_observed",
        "growth_client_snapshots",
        ["user_id", "observed_at"],
    )

    # Snapshot of competitor public profile metrics.
    op.create_table(
        "growth_competitor_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "competitor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("growth_competitors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_count_total", sa.Integer(), nullable=True),
        sa.Column("rating_avg", sa.Numeric(4, 2), nullable=True),
        sa.Column("posts_count_7d", sa.Integer(), nullable=True),
        sa.Column("posts_count_30d", sa.Integer(), nullable=True),
        sa.Column("services_count", sa.Integer(), nullable=True),
        sa.Column("data_source", sa.String(length=60), nullable=False, server_default="google_maps_public"),
        sa.Column("extraction_job_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("competitor_id", "observed_at", name="uq_growth_comp_snapshots_comp_observed"),
    )
    op.create_index(
        "ix_growth_competitor_snapshots_competitor_observed",
        "growth_competitor_snapshots",
        ["competitor_id", "observed_at"],
    )

    # Declared services for client snapshots.
    op.create_table(
        "growth_client_services_snapshot",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("service_name_normalized", sa.String(length=180), nullable=False),
        sa.Column("service_name_raw", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id",
            "observed_at",
            "service_name_normalized",
            name="uq_growth_client_services_user_observed_service",
        ),
    )
    op.create_index(
        "ix_growth_client_services_user_observed",
        "growth_client_services_snapshot",
        ["user_id", "observed_at"],
    )

    # Declared services for competitor snapshots.
    op.create_table(
        "growth_competitor_services_snapshot",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "competitor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("growth_competitors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("service_name_normalized", sa.String(length=180), nullable=False),
        sa.Column("service_name_raw", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "competitor_id",
            "observed_at",
            "service_name_normalized",
            name="uq_growth_comp_services_comp_observed_service",
        ),
    )
    op.create_index(
        "ix_growth_comp_services_competitor_observed",
        "growth_competitor_services_snapshot",
        ["competitor_id", "observed_at"],
    )

    # Keyword metrics for client's own review corpus by time period.
    op.create_table(
        "growth_client_keyword_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("keyword", sa.String(length=120), nullable=False),
        sa.Column("mentions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sentiment_positive_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("sentiment_neutral_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("sentiment_negative_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id",
            "period_start",
            "period_end",
            "keyword",
            name="uq_growth_client_keywords_user_period_keyword",
        ),
    )
    op.create_index(
        "ix_growth_client_keywords_user_period",
        "growth_client_keyword_metrics",
        ["user_id", "period_end", "mentions_count"],
    )

    # Keyword metrics for competitor review corpus by time period.
    op.create_table(
        "growth_competitor_keyword_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "competitor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("growth_competitors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("keyword", sa.String(length=120), nullable=False),
        sa.Column("mentions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sentiment_positive_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("sentiment_neutral_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("sentiment_negative_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "competitor_id",
            "period_start",
            "period_end",
            "keyword",
            name="uq_growth_comp_keywords_comp_period_keyword",
        ),
    )
    op.create_index(
        "ix_growth_comp_keywords_comp_period",
        "growth_competitor_keyword_metrics",
        ["competitor_id", "period_end", "mentions_count"],
    )

    # Materialized comparison rows (client vs competitor) for fast dashboard reads.
    op.create_table(
        "growth_benchmark_comparisons",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "competitor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("growth_competitors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rating_gap", sa.Numeric(5, 2), nullable=True),
        sa.Column("review_count_gap", sa.Integer(), nullable=True),
        sa.Column("review_growth_30d_gap", sa.Integer(), nullable=True),
        sa.Column("posting_freq_30d_gap", sa.Integer(), nullable=True),
        sa.Column("keyword_share_gap", sa.Numeric(6, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id",
            "competitor_id",
            "observed_at",
            name="uq_growth_benchmark_user_comp_observed",
        ),
    )
    op.create_index(
        "ix_growth_benchmark_user_observed",
        "growth_benchmark_comparisons",
        ["user_id", "observed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_growth_benchmark_user_observed", table_name="growth_benchmark_comparisons")
    op.drop_table("growth_benchmark_comparisons")

    op.drop_index("ix_growth_comp_keywords_comp_period", table_name="growth_competitor_keyword_metrics")
    op.drop_table("growth_competitor_keyword_metrics")

    op.drop_index("ix_growth_client_keywords_user_period", table_name="growth_client_keyword_metrics")
    op.drop_table("growth_client_keyword_metrics")

    op.drop_index("ix_growth_comp_services_competitor_observed", table_name="growth_competitor_services_snapshot")
    op.drop_table("growth_competitor_services_snapshot")

    op.drop_index("ix_growth_client_services_user_observed", table_name="growth_client_services_snapshot")
    op.drop_table("growth_client_services_snapshot")

    op.drop_index("ix_growth_competitor_snapshots_competitor_observed", table_name="growth_competitor_snapshots")
    op.drop_table("growth_competitor_snapshots")

    op.drop_index("ix_growth_client_snapshots_user_observed", table_name="growth_client_snapshots")
    op.drop_table("growth_client_snapshots")

    op.drop_index("ix_growth_competitors_user_id", table_name="growth_competitors")
    op.drop_table("growth_competitors")
