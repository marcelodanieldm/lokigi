"""add starter activation flags to google_connections

Revision ID: 20260418_0008
Revises: 20260418_0007
Create Date: 2026-04-18 18:30:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260418_0008"
down_revision: Union[str, None] = "20260418_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "google_connections",
        sa.Column("manual_approval_enabled", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.add_column(
        "google_connections",
        sa.Column("negative_review_whatsapp_enabled", sa.Boolean(), nullable=True, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("google_connections", "negative_review_whatsapp_enabled")
    op.drop_column("google_connections", "manual_approval_enabled")