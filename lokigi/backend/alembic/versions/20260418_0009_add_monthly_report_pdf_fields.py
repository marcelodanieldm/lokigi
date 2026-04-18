"""add monthly report pdf fields

Revision ID: 20260418_0009
Revises: 20260418_0008
Create Date: 2026-04-18 18:10:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260418_0009"
down_revision: Union[str, None] = "20260418_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("monthly_reports", sa.Column("executive_summary", sa.JSON(), nullable=True))
    op.add_column(
        "monthly_reports",
        sa.Column("pdf_status", sa.String(length=20), nullable=False, server_default="pending"),
    )
    op.add_column("monthly_reports", sa.Column("pdf_object_key", sa.Text(), nullable=True))
    op.add_column("monthly_reports", sa.Column("pdf_signed_url", sa.Text(), nullable=True))
    op.add_column(
        "monthly_reports",
        sa.Column("pdf_signed_url_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("monthly_reports", sa.Column("pdf_generated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("monthly_reports", sa.Column("pdf_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("monthly_reports", "pdf_error")
    op.drop_column("monthly_reports", "pdf_generated_at")
    op.drop_column("monthly_reports", "pdf_signed_url_expires_at")
    op.drop_column("monthly_reports", "pdf_signed_url")
    op.drop_column("monthly_reports", "pdf_object_key")
    op.drop_column("monthly_reports", "pdf_status")
    op.drop_column("monthly_reports", "executive_summary")
