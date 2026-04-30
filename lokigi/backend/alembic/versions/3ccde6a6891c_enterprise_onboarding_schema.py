"""enterprise_onboarding_schema

Adds extended branding / SMTP / onboarding-step columns to the
`organizations` table, and creates the `org_locations` table for
bulk-imported locations.

Revision ID: 3ccde6a6891c
Revises:     725354b510c4
Create Date: 2025-01-01

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# ── revision identifiers ───────────────────────────────────────────────────────
revision = "3ccde6a6891c"
down_revision = "725354b510c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. New columns on `organizations` ─────────────────────────────────────
    _add_col_if_missing = [
        # (column_name, DDL_fragment)
        ("font_family",       "TEXT DEFAULT 'Inter, sans-serif'"),
        ("isotipo_url",       "TEXT"),
        ("hide_lokigi_brand", "BOOLEAN NOT NULL DEFAULT false"),
        ("smtp_host",         "TEXT"),
        ("smtp_port",         "INTEGER DEFAULT 587"),
        ("smtp_user",         "TEXT"),
        ("smtp_password_enc", "TEXT"),
        ("smtp_use_tls",      "BOOLEAN NOT NULL DEFAULT true"),
        ("onboarding_step",   "INTEGER NOT NULL DEFAULT 1"),
    ]

    for col_name, col_ddl in _add_col_if_missing:
        conn.execute(sa.text(
            f"ALTER TABLE organizations ADD COLUMN IF NOT EXISTS {col_name} {col_ddl}"
        ))

    # ── 2. `org_locations` table ──────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS org_locations (
            id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id     UUID        NOT NULL
                           REFERENCES organizations(id) ON DELETE CASCADE,
            place_id   TEXT,
            address    TEXT,
            name       TEXT,
            phone      VARCHAR(64),
            city       VARCHAR(128),
            country    VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_org_location_place UNIQUE (org_id, place_id)
        )
    """))

    conn.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_org_locations_org_id ON org_locations (org_id)"
    ))


def downgrade() -> None:
    conn = op.get_bind()

    # Drop org_locations first (child table)
    conn.execute(sa.text("DROP TABLE IF EXISTS org_locations"))

    # Remove new columns from organizations
    drop_cols = [
        "font_family", "isotipo_url", "hide_lokigi_brand",
        "smtp_host", "smtp_port", "smtp_user", "smtp_password_enc",
        "smtp_use_tls", "onboarding_step",
    ]
    for col in drop_cols:
        conn.execute(sa.text(
            f"ALTER TABLE organizations DROP COLUMN IF EXISTS {col}"
        ))
