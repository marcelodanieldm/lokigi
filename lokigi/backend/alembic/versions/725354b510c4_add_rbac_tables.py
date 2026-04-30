"""add RBAC tables: roles, permissions, role_permissions, user_org_roles, user_location_access, audit_logs

Revision ID: 725354b510c4
Revises: 500dcc305670
Create Date: 2026-04-30 00:00:00.000000

What this migration does
------------------------
1. Creates the RBAC core tables:
     roles                  — canonical role definitions (4 rows)
     permissions            — granular permission strings
     role_permissions       — M2M: role → permission grants
     user_org_roles         — user's role inside a specific org
     user_location_access   — explicit location grants for Manager/Staff

2. Creates the audit_logs table (immutable append-only event log).

3. Seeds the 4 default roles + all permissions from ROLE_PERMISSIONS dict.

4. Adds covering indexes for the hot-path queries.

Rollback (downgrade)
--------------------
Drops all tables created above in reverse dependency order.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# ---------------------------------------------------------------------------

revision = "725354b510c4"
down_revision = "500dcc305670"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# UPGRADE
# ---------------------------------------------------------------------------

def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. roles ─────────────────────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS roles (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            slug        TEXT NOT NULL UNIQUE,
            label       TEXT NOT NULL,
            description TEXT,
            level       INTEGER NOT NULL DEFAULT 10
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_roles_slug ON roles (slug)"))

    # ── 2. permissions ────────────────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS permissions (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name        TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_permissions_name ON permissions (name)"))

    # ── 3. role_permissions ───────────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            role_id       UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
            CONSTRAINT uq_role_permissions UNIQUE (role_id, permission_id)
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_role_permissions_role_id ON role_permissions (role_id)"))

    # ── 4. user_org_roles ─────────────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS user_org_roles (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            role_id     UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
            invited_by  UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_user_org_role UNIQUE (user_id, org_id)
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_user_org_roles_org_id  ON user_org_roles (org_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_user_org_roles_user_id ON user_org_roles (user_id)"))

    # ── 5. user_location_access ───────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS user_location_access (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_org_role_id UUID NOT NULL REFERENCES user_org_roles(id) ON DELETE CASCADE,
            location_id      TEXT NOT NULL,
            granted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_user_location_access UNIQUE (user_org_role_id, location_id)
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_user_location_access_location_id ON user_location_access (location_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_user_location_access_user_org_role_id ON user_location_access (user_org_role_id)"))

    # ── 6. audit_logs ─────────────────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            actor_id      UUID REFERENCES users(id) ON DELETE SET NULL,
            actor_role    TEXT,
            action        TEXT NOT NULL,
            resource_type TEXT,
            resource_id   TEXT,
            details       JSONB,
            ip_address    TEXT,
            user_agent    TEXT,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_audit_logs_org_id_created_at ON audit_logs (org_id, created_at)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_id         ON audit_logs (actor_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_audit_logs_action           ON audit_logs (action)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_audit_logs_resource         ON audit_logs (resource_type, resource_id)"))

    # ── 7. Seed default roles + permissions ───────────────────────────────────
    _seed_roles_and_permissions(conn)


def _seed_roles_and_permissions(conn) -> None:
    from app.enterprise.rbac_models import ROLE_PERMISSIONS, RoleLevel

    roles_meta = [
        ("superadmin",      "SuperAdmin",      int(RoleLevel.SUPER_ADMIN)),
        ("network_manager", "Network Manager", int(RoleLevel.NETWORK_MANAGER)),
        ("store_manager",   "Store Manager",   int(RoleLevel.STORE_MANAGER)),
        ("store_staff",     "Store Staff",     int(RoleLevel.STORE_STAFF)),
    ]

    # Insert roles
    for slug, label, level in roles_meta:
        conn.execute(sa.text("""
            INSERT INTO roles (slug, label, level)
            VALUES (:slug, :label, :level)
            ON CONFLICT (slug) DO NOTHING
        """), {"slug": slug, "label": label, "level": level})

    # Collect all unique permission names
    all_perms: set[str] = set()
    for perms in ROLE_PERMISSIONS.values():
        all_perms.update(perms)

    # Insert permissions
    for perm_name in sorted(all_perms):
        conn.execute(sa.text("""
            INSERT INTO permissions (name)
            VALUES (:name)
            ON CONFLICT (name) DO NOTHING
        """), {"name": perm_name})

    # Link role_permissions
    for slug, perm_names in ROLE_PERMISSIONS.items():
        for perm_name in perm_names:
            conn.execute(sa.text("""
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM   roles r, permissions p
                WHERE  r.slug = :slug AND p.name = :perm
                ON CONFLICT ON CONSTRAINT uq_role_permissions DO NOTHING
            """), {"slug": slug, "perm": perm_name})


# ---------------------------------------------------------------------------
# DOWNGRADE
# ---------------------------------------------------------------------------

def downgrade() -> None:
    conn = op.get_bind()

    tables = [
        "audit_logs",
        "user_location_access",
        "user_org_roles",
        "role_permissions",
        "permissions",
        "roles",
    ]
    for t in tables:
        conn.execute(sa.text(f"DROP TABLE IF EXISTS {t} CASCADE"))
