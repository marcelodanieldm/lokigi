"""add starter_monthly_metrics table

Revision ID: 20260418_0003
Revises: 20260418_0002
Create Date: 2026-04-18 02:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260418_0003"
down_revision: Union[str, None] = "20260418_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "starter_monthly_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("location_id", sa.String(length=128), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("total_reviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_rating", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("response_rate_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("avg_response_time_minutes", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id", "year", "month",
            name="uq_starter_monthly_metrics_user_year_month",
        ),
    )
    op.create_index(
        "ix_starter_monthly_metrics_user_id",
        "starter_monthly_metrics",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_starter_monthly_metrics_user_id", table_name="starter_monthly_metrics")
    op.drop_table("starter_monthly_metrics")
