"""add ultralight competitor scrape tables

Revision ID: 20260418_0015
Revises: 20260418_0014
Create Date: 2026-04-18 23:58:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260418_0015"
down_revision: Union[str, None] = "20260418_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    competitor_status_enum = sa.Enum("active", "inactive", name="competitor_status_enum")
    scrape_status_enum = sa.Enum("running", "ok", "partial", "error", "blocked", name="scrape_status_enum")
    price_bucket_enum = sa.Enum("unknown", "budget", "mid", "premium", "luxury", name="price_bucket_enum")

    competitor_status_enum.create(op.get_bind(), checkfirst=True)
    scrape_status_enum.create(op.get_bind(), checkfirst=True)
    price_bucket_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "competitor",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url_hash", sa.String(length=40), nullable=False),
        sa.Column("maps_url", sa.Text(), nullable=False),
        sa.Column("name_short", sa.String(length=120), nullable=True),
        sa.Column("zone_code", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", competitor_status_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "url_hash", name="uq_competitor_user_url_hash"),
    )
    op.create_index("ix_competitor_user_zone", "competitor", ["user_id", "zone_code"])

    op.create_table(
        "scrape_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("status", scrape_status_enum, nullable=False, server_default="running"),
        sa.Column("total_targets", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_success", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scrape_run_user_started", "scrape_run", ["user_id", "started_at"])
    op.create_index("ix_scrape_run_status", "scrape_run", ["status", "started_at"])

    op.create_table(
        "competitor_snapshot",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scrape_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scrape_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("competitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("competitor.id", ondelete="CASCADE"), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("rating_x100", sa.Integer(), nullable=True),
        sa.Column("total_reviews", sa.Integer(), nullable=True),
        sa.Column("price_bucket", price_bucket_enum, nullable=False, server_default="unknown"),
        sa.Column("category_code", sa.Integer(), nullable=True),
        sa.Column("address_hash", sa.String(length=40), nullable=True),
        sa.Column("posts_30d", sa.Integer(), nullable=True),
        sa.Column("source_status", scrape_status_enum, nullable=False, server_default="ok"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("scrape_run_id", "competitor_id", name="uq_comp_snapshot_run_competitor"),
    )
    op.create_index("ix_comp_snapshot_competitor_date", "competitor_snapshot", ["competitor_id", "observed_on"])
    op.create_index("ix_comp_snapshot_status", "competitor_snapshot", ["source_status", "observed_on"])

    op.create_table(
        "service_catalog",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("label_short", sa.String(length=80), nullable=False),
        sa.UniqueConstraint("code", name="uq_service_catalog_code"),
    )

    op.create_table(
        "competitor_service_map",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("competitor_snapshot.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("service_catalog.id", ondelete="CASCADE"), nullable=False),
        sa.Column("present", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("snapshot_id", "service_id", name="uq_comp_service_map_snapshot_service"),
    )
    op.create_index("ix_comp_service_map_service", "competitor_service_map", ["service_id"])


def downgrade() -> None:
    op.drop_index("ix_comp_service_map_service", table_name="competitor_service_map")
    op.drop_table("competitor_service_map")

    op.drop_table("service_catalog")

    op.drop_index("ix_comp_snapshot_status", table_name="competitor_snapshot")
    op.drop_index("ix_comp_snapshot_competitor_date", table_name="competitor_snapshot")
    op.drop_table("competitor_snapshot")

    op.drop_index("ix_scrape_run_status", table_name="scrape_run")
    op.drop_index("ix_scrape_run_user_started", table_name="scrape_run")
    op.drop_table("scrape_run")

    op.drop_index("ix_competitor_user_zone", table_name="competitor")
    op.drop_table("competitor")

    price_bucket_enum = sa.Enum("unknown", "budget", "mid", "premium", "luxury", name="price_bucket_enum")
    scrape_status_enum = sa.Enum("running", "ok", "partial", "error", "blocked", name="scrape_status_enum")
    competitor_status_enum = sa.Enum("active", "inactive", name="competitor_status_enum")

    price_bucket_enum.drop(op.get_bind(), checkfirst=True)
    scrape_status_enum.drop(op.get_bind(), checkfirst=True)
    competitor_status_enum.drop(op.get_bind(), checkfirst=True)
