"""add google profile description snapshot

Revision ID: 20260429_0004
Revises: 20260418_0015, 20260429_0003
Create Date: 2026-04-29 00:04:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0004"
down_revision: Union[str, tuple[str, str], None] = ("20260418_0015", "20260429_0003")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("google_connections", sa.Column("google_profile_description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("google_connections", "google_profile_description")
