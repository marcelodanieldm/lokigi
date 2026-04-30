"""add org_id to tenanted tables + enterprise indexes

Revision ID: 500dcc305670
Revises: (set this to the current head revision in your project)
Create Date: 2026-01-01 00:00:00.000000

What this migration does
------------------------
1. Creates the `organizations` table (if it doesn't already exist from a
   previous migration — idempotent via IF NOT EXISTS).

2. Adds `org_id UUID REFERENCES organizations(id)` to:
   - google_connections
   - reviews

   NOTE: `users` are already linked to an org via `org_memberships`.
   Adding a direct org_id to `users` is intentionally omitted to avoid
   denormalisation — use the org_memberships join path instead.

3. Creates all performance indexes from enterprise_network_views.sql.

4. Does NOT add NOT NULL constraints on the new org_id columns: existing
   rows will have org_id = NULL.  The application layer (OrgMiddleware +
   apply_org_filter) enforces tenant isolation at query time; unowned rows
   simply fall outside all tenant scopes.

   To backfill existing rows, run the upgrade_data() helper below after
   you have created the organizations records and know the org_id values.

Rollback (downgrade)
--------------------
Removes indexes and columns added in upgrade().
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# ---------------------------------------------------------------------------

revision = "500dcc305670"
down_revision = None       # ← replace with your current head revision id
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# UPGRADE
# ---------------------------------------------------------------------------

def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. organizations table ───────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS organizations (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agency_name    TEXT NOT NULL,
            domain         TEXT,
            primary_color  TEXT NOT NULL DEFAULT '#7c3aed',
            secondary_color TEXT NOT NULL DEFAULT '#4f46e5',
            logo_url       TEXT,
            font_family    TEXT NOT NULL DEFAULT '''Inter'', sans-serif',
            hide_lokigi_brand BOOLEAN NOT NULL DEFAULT FALSE,
            plan           TEXT NOT NULL DEFAULT 'growth',
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_organizations_domain
            ON organizations (domain)
    """))

    # ── 2. org_memberships table ─────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS org_memberships (
            id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id    UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            user_id   TEXT NOT NULL UNIQUE,   -- matches users.id / google uid
            role      TEXT NOT NULL DEFAULT 'member',
            joined_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_org_memberships_org_id_user_id
            ON org_memberships (org_id, user_id)
    """))

    # ── 3. Add org_id to google_connections ──────────────────────────────────
    _add_org_id_column(conn, "google_connections")

    # ── 4. Add org_id to reviews ─────────────────────────────────────────────
    _add_org_id_column(conn, "reviews")

    # ── 5. Performance indexes ───────────────────────────────────────────────
    # NOTE: CONCURRENTLY cannot run inside a transaction block.
    # Alembic wraps upgrade() in a transaction by default.
    # We use CREATE INDEX (without CONCURRENTLY) here; for production with
    # large tables, run the CONCURRENTLY versions from enterprise_network_views.sql
    # manually after the migration.

    indexes = [
        "CREATE INDEX IF NOT EXISTS ix_reviews_location_id_create_time  ON reviews (location_id, create_time DESC)",
        "CREATE INDEX IF NOT EXISTS ix_reviews_connection_id_create_time ON reviews (connection_id, create_time DESC)",
        "CREATE INDEX IF NOT EXISTS ix_reviews_rating                    ON reviews (rating)",
        "CREATE INDEX IF NOT EXISTS ix_reviews_replied                   ON reviews (connection_id, create_time) WHERE reply_text IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS ix_reviews_reply_action              ON reviews (reply_action)",
        "CREATE INDEX IF NOT EXISTS ix_google_connections_user_id_location_id ON google_connections (user_id, location_id)",
        "CREATE INDEX IF NOT EXISTS ix_google_connections_covering       ON google_connections (id, user_id, location_id, business_name)",
    ]

    for ddl in indexes:
        conn.execute(sa.text(ddl))


# ---------------------------------------------------------------------------
# DOWNGRADE
# ---------------------------------------------------------------------------

def downgrade() -> None:
    conn = op.get_bind()

    # Drop indexes
    index_drops = [
        "DROP INDEX IF EXISTS ix_reviews_location_id_create_time",
        "DROP INDEX IF EXISTS ix_reviews_connection_id_create_time",
        "DROP INDEX IF EXISTS ix_reviews_rating",
        "DROP INDEX IF EXISTS ix_reviews_replied",
        "DROP INDEX IF EXISTS ix_reviews_reply_action",
        "DROP INDEX IF EXISTS ix_google_connections_user_id_location_id",
        "DROP INDEX IF EXISTS ix_google_connections_covering",
        "DROP INDEX IF EXISTS ix_org_memberships_org_id_user_id",
        "DROP INDEX IF EXISTS ix_organizations_domain",
    ]
    for ddl in index_drops:
        conn.execute(sa.text(ddl))

    # Drop org_id columns
    _drop_org_id_column(conn, "reviews")
    _drop_org_id_column(conn, "google_connections")

    # Drop tables (cascade handles FK references)
    conn.execute(sa.text("DROP TABLE IF EXISTS org_memberships CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS organizations CASCADE"))


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _add_org_id_column(conn, table: str) -> None:
    """Add org_id UUID FK column to `table` if it doesn't already exist."""
    exists = conn.execute(sa.text(
        f"""
        SELECT 1
        FROM   information_schema.columns
        WHERE  table_name = '{table}'
          AND  column_name = 'org_id'
        """
    )).fetchone()
    if exists:
        return  # idempotent

    conn.execute(sa.text(f"""
        ALTER TABLE {table}
        ADD COLUMN org_id UUID
            REFERENCES organizations(id)
            ON DELETE SET NULL
    """))

    conn.execute(sa.text(f"""
        CREATE INDEX IF NOT EXISTS ix_{table}_org_id
            ON {table} (org_id)
        WHERE org_id IS NOT NULL
    """))


def _drop_org_id_column(conn, table: str) -> None:
    conn.execute(sa.text(f"""
        ALTER TABLE {table} DROP COLUMN IF EXISTS org_id
    """))
