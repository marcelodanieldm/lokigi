"""add growth premium kpi tables

Revision ID: 20260418_0013
Revises: 20260418_0012
Create Date: 2026-04-18 20:15:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260418_0013"
down_revision: Union[str, None] = "20260418_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("growth_client_snapshots", sa.Column("photos_count_total", sa.Integer(), nullable=True))
    op.add_column("growth_competitor_snapshots", sa.Column("photos_count_total", sa.Integer(), nullable=True))

    op.create_table(
        "growth_serp_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "competitor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("growth_competitors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("keyword", sa.String(length=120), nullable=False),
        sa.Column("location_label", sa.String(length=140), nullable=False, server_default="default"),
        sa.Column("entity_type", sa.String(length=20), nullable=False, server_default="client"),
        sa.Column("rank_position", sa.Integer(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_growth_serp_observations_user_observed",
        "growth_serp_observations",
        ["user_id", "observed_at"],
    )
    op.create_index(
        "ix_growth_serp_observations_user_keyword",
        "growth_serp_observations",
        ["user_id", "keyword"],
    )

    op.create_table(
        "growth_keyword_conquest_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("keyword", sa.String(length=120), nullable=False),
        sa.Column("location_label", sa.String(length=140), nullable=False, server_default="default"),
        sa.Column(
            "displaced_competitor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("growth_competitors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("previous_rank", sa.Integer(), nullable=True),
        sa.Column("new_rank", sa.Integer(), nullable=True),
        sa.Column("conquered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_growth_keyword_conquest_user_conquered",
        "growth_keyword_conquest_events",
        ["user_id", "conquered_at"],
    )
    op.create_index(
        "ix_growth_keyword_conquest_user_keyword",
        "growth_keyword_conquest_events",
        ["user_id", "keyword"],
    )

    op.execute(
        """
        CREATE VIEW growth_posting_rank_correlation AS
        WITH client_rank AS (
            SELECT
                user_id,
                date_trunc('day', observed_at) AS observed_day,
                AVG(rank_position)::numeric AS avg_client_rank
            FROM growth_serp_observations
            WHERE entity_type = 'client'
            GROUP BY user_id, date_trunc('day', observed_at)
        ),
        competitor_posts AS (
            SELECT
                gc.user_id,
                date_trunc('day', gcs.observed_at) AS observed_day,
                AVG(COALESCE(gcs.posts_count_30d, 0))::numeric AS avg_comp_posts_30d
            FROM growth_competitor_snapshots gcs
            JOIN growth_competitors gc ON gc.id = gcs.competitor_id
            GROUP BY gc.user_id, date_trunc('day', gcs.observed_at)
        )
        SELECT
            cp.user_id,
            corr(cp.avg_comp_posts_30d::float, cr.avg_client_rank::float) AS posting_rank_correlation,
            COUNT(*)::int AS samples,
            NOW() AS computed_at
        FROM competitor_posts cp
        JOIN client_rank cr
            ON cr.user_id = cp.user_id
           AND cr.observed_day = cp.observed_day
        GROUP BY cp.user_id
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS growth_posting_rank_correlation")

    op.drop_index("ix_growth_keyword_conquest_user_keyword", table_name="growth_keyword_conquest_events")
    op.drop_index("ix_growth_keyword_conquest_user_conquered", table_name="growth_keyword_conquest_events")
    op.drop_table("growth_keyword_conquest_events")

    op.drop_index("ix_growth_serp_observations_user_keyword", table_name="growth_serp_observations")
    op.drop_index("ix_growth_serp_observations_user_observed", table_name="growth_serp_observations")
    op.drop_table("growth_serp_observations")

    op.drop_column("growth_competitor_snapshots", "photos_count_total")
    op.drop_column("growth_client_snapshots", "photos_count_total")
