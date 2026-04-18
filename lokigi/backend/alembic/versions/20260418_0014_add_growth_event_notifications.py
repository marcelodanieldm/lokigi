"""add growth event notifications table

Revision ID: 20260418_0014
Revises: 20260418_0013
Create Date: 2026-04-18 23:20:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260418_0014"
down_revision: Union[str, None] = "20260418_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "growth_event_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("severity", sa.String(length=12), nullable=False, server_default="medium"),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("report_url", sa.Text(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("send_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("is_seen", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_growth_event_notifications_user_created",
        "growth_event_notifications",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_growth_event_notifications_status_created",
        "growth_event_notifications",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_growth_event_notifications_dedupe_created",
        "growth_event_notifications",
        ["dedupe_key", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_growth_event_notifications_dedupe_created", table_name="growth_event_notifications")
    op.drop_index("ix_growth_event_notifications_status_created", table_name="growth_event_notifications")
    op.drop_index("ix_growth_event_notifications_user_created", table_name="growth_event_notifications")
    op.drop_table("growth_event_notifications")
