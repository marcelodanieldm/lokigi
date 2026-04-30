"""enterprise_offboarding_schema

Revision ID: 93b87f588229
Revises: 3ccde6a6891c
Create Date: 2025-01-01 00:00:00.000000

Adds:
  - organizations.org_status           VARCHAR(32) NOT NULL DEFAULT 'active'
  - organizations.deletion_scheduled_at TIMESTAMPTZ NULL

Creates:
  - partner_offboarding_surveys        — qualitative exit-survey answers
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision      = "93b87f588229"
down_revision = "3ccde6a6891c"
branch_labels = None
depends_on    = None


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. Add lifecycle status to organizations ──────────────────────────────
    bind.execute(sa.text("""
        ALTER TABLE organizations
            ADD COLUMN IF NOT EXISTS org_status VARCHAR(32) NOT NULL DEFAULT 'active';
    """))

    bind.execute(sa.text("""
        ALTER TABLE organizations
            ADD COLUMN IF NOT EXISTS deletion_scheduled_at TIMESTAMPTZ NULL;
    """))

    # Optional CHECK constraint — safe to skip if already exists
    try:
        bind.execute(sa.text("""
            ALTER TABLE organizations
                ADD CONSTRAINT chk_org_status
                CHECK (org_status IN ('active','hibernating','pending_deletion','cancelled'));
        """))
    except Exception:
        pass  # constraint already exists

    # ── 2. Create partner_offboarding_surveys ─────────────────────────────────
    bind.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS partner_offboarding_surveys (
            id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id             UUID        NOT NULL
                                           REFERENCES organizations(id)
                                           ON DELETE SET NULL,
            reason_primary     TEXT,
            score_support      INTEGER     CHECK (score_support BETWEEN 1 AND 10),
            score_scalability  INTEGER     CHECK (score_scalability BETWEEN 1 AND 10),
            score_roi          INTEGER     CHECK (score_roi BETWEEN 1 AND 10),
            open_feedback      TEXT,
            would_recommend    BOOLEAN     NOT NULL DEFAULT false,
            created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """))

    bind.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_partner_surveys_org_id
            ON partner_offboarding_surveys (org_id);
    """))


def downgrade() -> None:
    bind = op.get_bind()

    bind.execute(sa.text("DROP TABLE IF EXISTS partner_offboarding_surveys;"))

    bind.execute(sa.text("""
        ALTER TABLE organizations
            DROP CONSTRAINT IF EXISTS chk_org_status;
    """))

    bind.execute(sa.text("""
        ALTER TABLE organizations
            DROP COLUMN IF EXISTS deletion_scheduled_at;
    """))

    bind.execute(sa.text("""
        ALTER TABLE organizations
            DROP COLUMN IF EXISTS org_status;
    """))
