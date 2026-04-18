"""add growth seo suggestions and alerts

Revision ID: 20260418_0012
Revises: 20260418_0011
Create Date: 2026-04-18 23:55:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision: str = "20260418_0012"
down_revision: Union[str, None] = "20260418_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "growth_seo_suggestions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("suggestion_type", sa.String(length=30), nullable=False),
        sa.Column("keyword", sa.String(length=120), nullable=False),
        sa.Column("current_text", sa.Text(), nullable=True),
        sa.Column("suggested_text", sa.Text(), nullable=False),
        sa.Column("keywords_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("justification_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("risk_level", sa.String(length=10), nullable=False, server_default="medio"),
        sa.Column("priority_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_period_start", sa.Date(), nullable=True),
        sa.Column("source_period_end", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_growth_seo_suggestions_user_status",
        "growth_seo_suggestions",
        ["user_id", "status", "created_at"],
    )

    op.create_table(
        "growth_seo_suggestion_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "suggestion_id",
            UUID(as_uuid=True),
            sa.ForeignKey("growth_seo_suggestions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ok"),
        sa.Column("request_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("response_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_growth_seo_suggestion_actions_suggestion_created",
        "growth_seo_suggestion_actions",
        ["suggestion_id", "created_at"],
    )
    op.create_index(
        "ix_growth_seo_suggestion_actions_user_action",
        "growth_seo_suggestion_actions",
        ["user_id", "action_type", "created_at"],
    )

    op.create_table(
        "growth_seo_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "suggestion_id",
            UUID(as_uuid=True),
            sa.ForeignKey("growth_seo_suggestions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=140), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=12), nullable=False, server_default="medium"),
        sa.Column("is_seen", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_growth_seo_alerts_user_seen_created",
        "growth_seo_alerts",
        ["user_id", "is_seen", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_growth_seo_alerts_user_seen_created", table_name="growth_seo_alerts")
    op.drop_table("growth_seo_alerts")

    op.drop_index("ix_growth_seo_suggestion_actions_user_action", table_name="growth_seo_suggestion_actions")
    op.drop_index(
        "ix_growth_seo_suggestion_actions_suggestion_created",
        table_name="growth_seo_suggestion_actions",
    )
    op.drop_table("growth_seo_suggestion_actions")

    op.drop_index("ix_growth_seo_suggestions_user_status", table_name="growth_seo_suggestions")
    op.drop_table("growth_seo_suggestions")
