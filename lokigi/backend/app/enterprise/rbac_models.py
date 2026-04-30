"""
backend/app/enterprise/rbac_models.py
========================================
Role-Based Access Control (RBAC) for Lokigi Enterprise.

Hierarchy (highest → lowest privilege):
  SuperAdmin      → full org control (white-label, billing, user management)
  NetworkManager  → all locations (bulk publish, consolidated reports, crisis)
  StoreManager    → assigned locations (competitive radar, approve replies)
  StoreStaff      → single location (reply reviews — no global metrics)

Tables
------
  roles                 — canonical role definitions
  permissions           — granular permission strings
  role_permissions      — M2M: which permissions each role has
  user_org_roles        — user's role inside a specific org
  user_location_access  — explicit location grants for Manager/Staff

Usage
-----
    from app.enterprise.rbac_models import has_permission, RoleLevel

    # Check inside a FastAPI route (after RoleChecker dependency runs)
    if not has_permission(current_user.id, "bulk_publish", db, org_id=org.id):
        raise HTTPException(403)

    # Hierarchy check (faster — no DB read for permissions)
    if RoleLevel.from_str(membership.role) >= RoleLevel.NETWORK_MANAGER:
        ...
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    select,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.database import Base


# ─── Role hierarchy enum ──────────────────────────────────────────────────────

class RoleLevel(enum.IntEnum):
    """Numeric hierarchy: higher value = more privilege."""
    STORE_STAFF      = 10
    STORE_MANAGER    = 20
    NETWORK_MANAGER  = 30
    SUPER_ADMIN      = 40

    @classmethod
    def from_str(cls, role: str) -> "RoleLevel":
        mapping = {
            "store_staff":      cls.STORE_STAFF,
            "store_manager":    cls.STORE_MANAGER,
            "network_manager":  cls.NETWORK_MANAGER,
            "superadmin":       cls.SUPER_ADMIN,
        }
        return mapping.get(role.lower(), cls.STORE_STAFF)

    def label(self) -> str:
        return {
            self.STORE_STAFF:     "Store Staff",
            self.STORE_MANAGER:   "Store Manager",
            self.NETWORK_MANAGER: "Network Manager",
            self.SUPER_ADMIN:     "SuperAdmin",
        }[self]

    def badge_color(self) -> str:
        """Tailwind CSS color class for role badge."""
        return {
            self.STORE_STAFF:     "stone",
            self.STORE_MANAGER:   "blue",
            self.NETWORK_MANAGER: "violet",
            self.SUPER_ADMIN:     "amber",
        }[self]


# ─── Default permission set per role ─────────────────────────────────────────

#: These are seeded into the DB on first run (see seed_default_permissions()).
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "superadmin": [
        # Org management
        "org.white_label.manage",
        "org.billing.manage",
        "org.users.invite",
        "org.users.remove",
        "org.users.role_change",
        "org.settings.manage",
        # All lower-level perms
        "locations.view_all",
        "locations.bulk_publish",
        "locations.bulk_reply",
        "reports.consolidated",
        "reports.export",
        "crisis.escalation.manage",
        "crisis.escalation.silence",
        "reviews.approve",
        "reviews.reply",
        "reviews.view",
        "competitor.radar.view",
        "audit.logs.view",
    ],
    "network_manager": [
        "locations.view_all",
        "locations.bulk_publish",
        "locations.bulk_reply",
        "reports.consolidated",
        "reports.export",
        "crisis.escalation.manage",
        "crisis.escalation.silence",
        "reviews.approve",
        "reviews.reply",
        "reviews.view",
        "competitor.radar.view",
        "audit.logs.view",
    ],
    "store_manager": [
        "locations.view_assigned",
        "reports.export",           # only for their locations
        "reviews.approve",
        "reviews.reply",
        "reviews.view",
        "competitor.radar.view",
    ],
    "store_staff": [
        "locations.view_assigned",
        "reviews.reply",
        "reviews.view",
    ],
}


# ─── SQLAlchemy Models ────────────────────────────────────────────────────────

class Role(Base):
    """
    Canonical role record.  Populated once via seed_default_permissions().
    slug = "superadmin" | "network_manager" | "store_manager" | "store_staff"
    """
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[int] = mapped_column(nullable=False, default=10)  # RoleLevel value

    permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )
    user_org_roles: Mapped[list["UserOrgRole"]] = relationship(back_populates="role")


class Permission(Base):
    """
    Granular permission string, e.g. 'locations.bulk_publish'.
    name is the stable dotted identifier used in code.
    """
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class RolePermission(Base):
    """M2M: Role ↔ Permission."""
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    )

    role: Mapped[Role] = relationship(back_populates="permissions")
    permission: Mapped[Permission] = relationship()


class UserOrgRole(Base):
    """
    Links a User to an Organization with a specific Role.
    Supersedes OrgMembership.role for granular permission control.
    OrgMembership is kept for backwards compatibility; this table adds RBAC.
    """
    __tablename__ = "user_org_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "org_id", name="uq_user_org_role"),
        Index("ix_user_org_roles_org_id", "org_id"),
        Index("ix_user_org_roles_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    role: Mapped[Role] = relationship(back_populates="user_org_roles", foreign_keys=[role_id])
    location_access: Mapped[list["UserLocationAccess"]] = relationship(
        back_populates="user_org_role", cascade="all, delete-orphan"
    )


class UserLocationAccess(Base):
    """
    Explicit location grants for StoreManager / StoreStaff.
    SuperAdmin and NetworkManager have implicit access to all locations
    (enforced in code — no rows needed here for them).
    """
    __tablename__ = "user_location_access"
    __table_args__ = (
        UniqueConstraint(
            "user_org_role_id", "location_id", name="uq_user_location_access"
        ),
        Index("ix_user_location_access_location_id", "location_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_org_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_org_roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[str] = mapped_column(String(128), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    user_org_role: Mapped[UserOrgRole] = relationship(back_populates="location_access")


# ─── has_permission() ─────────────────────────────────────────────────────────

def has_permission(
    user_id: uuid.UUID,
    permission_name: str,
    db: Session,
    *,
    org_id: uuid.UUID | None = None,
) -> bool:
    """
    Return True if `user_id` holds `permission_name` inside `org_id`.

    Algorithm:
      1. Find the user's UserOrgRole for this org.
      2. Load the role's permissions (cached on the Role object via eager load
         in practice — a second call within the same session hits the identity map).
      3. Check if any Permission.name matches `permission_name`.

    Falls back to hierarchy-based check if the permissions table hasn't been
    seeded yet (graceful degradation).

    Parameters
    ----------
    user_id:
        UUID of the authenticated user.
    permission_name:
        Dotted permission string, e.g. "locations.bulk_publish".
    db:
        Active SQLAlchemy Session.
    org_id:
        UUID of the organization context.  If None, returns False.
    """
    if org_id is None:
        return False

    # Fetch UserOrgRole with Role + Permissions in one query
    stmt = (
        select(UserOrgRole)
        .join(UserOrgRole.role)
        .where(
            UserOrgRole.user_id == user_id,
            UserOrgRole.org_id == org_id,
        )
    )
    user_role = db.scalars(stmt).first()
    if user_role is None:
        return False

    # Load permissions for this role
    perm_stmt = (
        select(Permission.name)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id == user_role.role_id)
    )
    perm_names: Sequence[str] = db.scalars(perm_stmt).all()

    if perm_names:
        return permission_name in perm_names

    # Graceful fallback: use in-memory ROLE_PERMISSIONS dict
    role_slug = db.scalars(
        select(Role.slug).where(Role.id == user_role.role_id)
    ).first() or "store_staff"
    return permission_name in ROLE_PERMISSIONS.get(role_slug, [])


def user_can_access_location(
    user_id: uuid.UUID,
    location_id: str,
    db: Session,
    *,
    org_id: uuid.UUID,
) -> bool:
    """
    Return True if the user may access `location_id`.

    SuperAdmin / NetworkManager → always True (all locations).
    StoreManager / StoreStaff  → must have a UserLocationAccess row.
    """
    stmt = (
        select(UserOrgRole)
        .join(UserOrgRole.role)
        .where(
            UserOrgRole.user_id == user_id,
            UserOrgRole.org_id == org_id,
        )
    )
    user_role = db.scalars(stmt).first()
    if user_role is None:
        return False

    role_slug = db.scalars(
        select(Role.slug).where(Role.id == user_role.role_id)
    ).first() or "store_staff"
    level = RoleLevel.from_str(role_slug)

    # High-privilege roles have blanket access
    if level >= RoleLevel.NETWORK_MANAGER:
        return True

    # Lower roles need explicit grant
    access = db.scalars(
        select(UserLocationAccess).where(
            UserLocationAccess.user_org_role_id == user_role.id,
            UserLocationAccess.location_id == location_id,
        )
    ).first()
    return access is not None


# ─── Seed helper ─────────────────────────────────────────────────────────────

def seed_default_permissions(db: Session) -> None:
    """
    Idempotently insert Role + Permission + RolePermission rows.
    Call once from an Alembic migration data_upgrade or a startup hook.
    """
    roles_meta = [
        ("superadmin",      "SuperAdmin",      RoleLevel.SUPER_ADMIN),
        ("network_manager", "Network Manager", RoleLevel.NETWORK_MANAGER),
        ("store_manager",   "Store Manager",   RoleLevel.STORE_MANAGER),
        ("store_staff",     "Store Staff",     RoleLevel.STORE_STAFF),
    ]

    # Upsert roles
    role_objs: dict[str, Role] = {}
    for slug, label, level in roles_meta:
        obj = db.scalars(select(Role).where(Role.slug == slug)).first()
        if obj is None:
            obj = Role(slug=slug, label=label, level=int(level))
            db.add(obj)
            db.flush()
        role_objs[slug] = obj

    # Upsert permissions + role_permissions
    for slug, perm_names in ROLE_PERMISSIONS.items():
        role = role_objs[slug]
        for perm_name in perm_names:
            # Upsert permission
            perm = db.scalars(
                select(Permission).where(Permission.name == perm_name)
            ).first()
            if perm is None:
                perm = Permission(name=perm_name)
                db.add(perm)
                db.flush()

            # Upsert role_permission link
            existing = db.scalars(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == perm.id,
                )
            ).first()
            if existing is None:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    db.commit()
