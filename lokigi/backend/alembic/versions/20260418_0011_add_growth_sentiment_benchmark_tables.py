"""add growth sentiment benchmark tables

Revision ID: 20260418_0011
Revises: 20260418_0010
Create Date: 2026-04-18 23:30:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision: str = "20260418_0011"
down_revision: Union[str, None] = "20260418_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "growth_sentiment_benchmark_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("window_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ok"),
        sa.Column("client_sentiment_score", sa.Numeric(6, 3), nullable=True),
        sa.Column("competitor_average_sentiment_score", sa.Numeric(6, 3), nullable=True),
        sa.Column("client_negative_rate", sa.Numeric(6, 3), nullable=True),
        sa.Column("rank_client_among_6", sa.Integer(), nullable=True),
        sa.Column("summary_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("diagnostics_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_growth_sentiment_benchmark_runs_user_created",
        "growth_sentiment_benchmark_runs",
        ["user_id", "created_at"],
    )

    op.create_table(
        "growth_sentiment_benchmark_topic_gaps",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            UUID(as_uuid=True),
            sa.ForeignKey("growth_sentiment_benchmark_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic", sa.String(length=120), nullable=False),
        sa.Column("client_complaint_rate", sa.Numeric(6, 3), nullable=True),
        sa.Column("competitor_complaint_rate", sa.Numeric(6, 3), nullable=True),
        sa.Column("gap", sa.Numeric(6, 3), nullable=True),
        sa.Column("support_competitors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("label", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 3), nullable=True),
        sa.Column("evidence_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_growth_sentiment_benchmark_topic_gaps_run",
        "growth_sentiment_benchmark_topic_gaps",
        ["run_id"],
    )
    op.create_index(
        "ix_growth_sentiment_benchmark_topic_gaps_user_label",
        "growth_sentiment_benchmark_topic_gaps",
        ["user_id", "label"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_growth_sentiment_benchmark_topic_gaps_user_label",
        table_name="growth_sentiment_benchmark_topic_gaps",
    )
    op.drop_index(
        "ix_growth_sentiment_benchmark_topic_gaps_run",
        table_name="growth_sentiment_benchmark_topic_gaps",
    )
    op.drop_table("growth_sentiment_benchmark_topic_gaps")

    op.drop_index(
        "ix_growth_sentiment_benchmark_runs_user_created",
        table_name="growth_sentiment_benchmark_runs",
    )
    op.drop_table("growth_sentiment_benchmark_runs")
