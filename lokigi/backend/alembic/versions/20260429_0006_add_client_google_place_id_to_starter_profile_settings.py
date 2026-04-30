"""add client_google_place_id to starter profile settings

Revision ID: 20260429_0006
Revises: 20260429_0005
Create Date: 2026-04-29 18:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_0006"
down_revision = "20260429_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "starter_profile_settings",
        sa.Column("client_google_place_id", sa.String(length=128), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("starter_profile_settings", "client_google_place_id")