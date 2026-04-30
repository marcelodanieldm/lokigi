"""add focus keywords to starter profile settings

Revision ID: 20260429_0005
Revises: 20260429_0004
Create Date: 2026-04-29 10:20:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0005"
down_revision: Union[str, tuple[str, str], None] = "20260429_00042"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "starter_profile_settings",
        sa.Column("focus_keywords", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column("starter_profile_settings", "focus_keywords", server_default=None)


def downgrade() -> None:
    op.drop_column("starter_profile_settings", "focus_keywords")