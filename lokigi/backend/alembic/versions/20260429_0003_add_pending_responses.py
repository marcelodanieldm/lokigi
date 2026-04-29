"""add pending responses table

Revision ID: 20260429_0003
Revises: 20260418_0002
Create Date: 2026-04-29 00:03:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260429_0003"
down_revision: Union[str, None] = "20260418_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pending_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_pk", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("tone", sa.String(length=50), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("approved_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["review_pk"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("review_pk", name="uq_pending_responses_review_pk"),
    )
    op.create_index("ix_pending_responses_status", "pending_responses", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pending_responses_status", table_name="pending_responses")
    op.drop_table("pending_responses")