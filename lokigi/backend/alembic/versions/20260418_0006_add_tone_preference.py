"""add preferred_tone to google_connections

Revision ID: 20260418_0006
Revises: 20260418_0005
Create Date: 2026-04-18 07:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260418_0006"
down_revision: Union[str, None] = "20260418_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "google_connections",
        sa.Column("preferred_tone", sa.String(50), nullable=True, server_default="cercano"),
    )


def downgrade() -> None:
    op.drop_column("google_connections", "preferred_tone")
