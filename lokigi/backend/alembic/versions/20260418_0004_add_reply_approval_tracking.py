"""add reply approval tracking columns

Revision ID: 20260418_0004
Revises: 20260418_0003
Create Date: 2026-04-18 03:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260418_0004"
down_revision: Union[str, None] = "20260418_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("reply_approved_text", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("reply_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "reply_sent_at")
    op.drop_column("reviews", "reply_approved_text")
