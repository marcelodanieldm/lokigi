"""add monthly_reports table

Revision ID: 20260418_0005
Revises: 20260418_0004
Create Date: 2026-04-18 06:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260418_0005"
down_revision: Union[str, None] = "20260418_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monthly_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "year", "month", name="uq_monthly_reports_user_year_month"),
    )
    op.create_index("ix_monthly_reports_user_id", "monthly_reports", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_monthly_reports_user_id", table_name="monthly_reports")
    op.drop_table("monthly_reports")
