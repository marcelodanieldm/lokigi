"""add review reply decision fields

Revision ID: 20260418_0002
Revises: 20260418_0001
Create Date: 2026-04-18 01:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260418_0002"
down_revision: Union[str, None] = "20260418_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("google_connections", sa.Column("business_name", sa.String(length=255), nullable=True))

    op.add_column("reviews", sa.Column("reply_action", sa.String(length=32), nullable=True))
    op.add_column("reviews", sa.Column("reply_detected_language", sa.String(length=16), nullable=True))
    op.add_column("reviews", sa.Column("reply_reason", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("reply_public_text", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("reply_alert_priority", sa.String(length=16), nullable=True))
    op.add_column("reviews", sa.Column("reply_alert_category", sa.String(length=32), nullable=True))
    op.add_column("reviews", sa.Column("reply_alert_summary", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("reply_alert_next_step", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("reply_decided_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "reply_decided_at")
    op.drop_column("reviews", "reply_alert_next_step")
    op.drop_column("reviews", "reply_alert_summary")
    op.drop_column("reviews", "reply_alert_category")
    op.drop_column("reviews", "reply_alert_priority")
    op.drop_column("reviews", "reply_public_text")
    op.drop_column("reviews", "reply_reason")
    op.drop_column("reviews", "reply_detected_language")
    op.drop_column("reviews", "reply_action")

    op.drop_column("google_connections", "business_name")
