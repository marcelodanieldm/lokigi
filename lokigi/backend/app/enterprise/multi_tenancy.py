"""
backend/app/enterprise/multi_tenancy.py
=========================================
Multi-Tenancy support for Lokigi Enterprise.

Architecture
------------
- `Organization` — top-level tenant record.  Every User and GoogleConnection
  belongs to exactly one org.
- `OrgMiddleware` — FastAPI middleware that resolves the current org from the
  authenticated user and attaches it to `request.state`.  All downstream DB
  queries call `apply_org_filter(stmt, org_id)` so data never leaks across
  tenants.
- Alembic migration helper included at the bottom of the file.

Usage (in a FastAPI route)
--------------------------
    from app.enterprise.multi_tenancy import get_current_org, apply_org_filter
    from app.models import GoogleConnection

    @router.get("/locations")
    def list_locations(
        org: Organization = Depends(get_current_org),
        db: Session = Depends(get_db),
    ):
        stmt = apply_org_filter(select(GoogleConnection), org.id)
        return db.scalars(stmt).all()
"""
from __future__ import annotations

import logging
import uuid
from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.database import Base, get_db
from app.models import User

logger = logging.getLogger(__name__)


# ─── Model ────────────────────────────────────────────────────────────────────

class Organization(Base):
    """Top-level tenant.  One organization = one agency / enterprise client."""
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # White-label theme — consumed by ThemeService
    primary_color: Mapped[str] = mapped_column(String(32), nullable=False, default="#7c3aed")
    secondary_color: Mapped[str] = mapped_column(String(32), nullable=False, default="#4f46e5")
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    agency_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agency_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    users: Mapped[list["OrgMembership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class OrgMembership(Base):
    """M2M bridge: a User belongs to exactly one Organization with a role."""
    __tablename__ = "org_memberships"
    __table_args__ = (
        Index("ix_org_memberships_user_id", "user_id"),
        Index("ix_org_memberships_org_id", "org_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,          # one user → one org
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default="member"
    )  # "superadmin" | "admin" | "member" | "viewer"

    organization: Mapped[Organization] = relationship(back_populates="users")
    user: Mapped[User] = relationship()


# ─── Middleware ───────────────────────────────────────────────────────────────

_ORG_HEADER = "X-Org-Id"   # optional explicit override (for internal services)
_USER_ID_HEADER = "X-User-Id"  # set by the auth layer upstream


class OrgMiddleware(BaseHTTPMiddleware):
    """
    Attaches `request.state.org_id` (UUID | None) on every request.

    Resolution order:
      1. `X-Org-Id` header  (trusted internal calls only — validate in prod
         by checking it comes from a known IP / service account)
      2. Look up the authenticated user's OrgMembership
      3. None  (unauthenticated or public routes)
    """

    def __init__(self, app, trusted_service_token: str | None = None) -> None:
        super().__init__(app)
        self._trusted_token = trusted_service_token

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request.state.org_id = None

        # 1. Explicit override (internal service-to-service calls)
        explicit_org = request.headers.get(_ORG_HEADER)
        svc_token = request.headers.get("X-Service-Token")
        if explicit_org and svc_token == self._trusted_token:
            try:
                request.state.org_id = uuid.UUID(explicit_org)
            except ValueError:
                pass  # malformed — ignore
            return await call_next(request)

        # 2. Resolve from authenticated user
        user_id_str = request.headers.get(_USER_ID_HEADER)
        if user_id_str:
            try:
                user_id = uuid.UUID(user_id_str)
                # We need a sync DB session inside an async middleware.
                # Use the sync SessionLocal directly (FastAPI's get_db is a generator).
                from app.database import SessionLocal  # avoid circular at module level
                if SessionLocal is not None:
                    with SessionLocal() as db:
                        membership = db.scalars(
                            select(OrgMembership).where(OrgMembership.user_id == user_id)
                        ).first()
                        if membership:
                            request.state.org_id = membership.org_id
            except (ValueError, Exception) as exc:
                logger.debug("OrgMiddleware: could not resolve org for user %s: %s", user_id_str, exc)

        return await call_next(request)


# ─── Dependency helpers ───────────────────────────────────────────────────────

def get_org_id(request: Request) -> uuid.UUID | None:
    """FastAPI dependency: returns the current org_id or None."""
    return getattr(request.state, "org_id", None)


def require_org_id(org_id: uuid.UUID | None = Depends(get_org_id)) -> uuid.UUID:
    """FastAPI dependency: raises 403 if no org is resolved."""
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No organization context. Ensure you are authenticated and belong to an organization.",
        )
    return org_id


def get_current_org(
    org_id: uuid.UUID = Depends(require_org_id),
    db: Session = Depends(get_db),
) -> Organization:
    """FastAPI dependency: returns the full Organization ORM object."""
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found.",
        )
    return org


# ─── Query filter helper ──────────────────────────────────────────────────────

def apply_org_filter(stmt, org_id: uuid.UUID):
    """
    Restrict a SQLAlchemy SELECT statement to rows belonging to `org_id`.

    The function walks the FROM clause looking for tables that have a direct
    `org_id` column.  For tables that reach the org through a join (e.g.
    GoogleConnection → OrgMembership), the caller should add the join manually
    before calling this helper, or use the convenience wrappers below.

    Example
    -------
        stmt = apply_org_filter(
            select(GoogleConnection)
            .join(OrgMembership, OrgMembership.user_id == GoogleConnection.user_id),
            org_id,
        )
    """
    # Inspect the primary entity of the statement
    entity = stmt.columns_clause_froms[0] if stmt.columns_clause_froms else None
    if entity is not None and hasattr(entity, "c") and "org_id" in entity.c:
        return stmt.where(entity.c.org_id == org_id)

    # Fallback: add a sub-select join through OrgMembership.user_id
    # Works for any table that has a `user_id` FK column.
    if entity is not None and hasattr(entity, "c") and "user_id" in entity.c:
        return stmt.where(
            entity.c.user_id.in_(
                select(OrgMembership.user_id).where(OrgMembership.org_id == org_id)
            )
        )

    logger.warning(
        "apply_org_filter: could not automatically filter %s — "
        "add the OrgMembership join manually.",
        entity,
    )
    return stmt


# ─── Registration helper (call from app factory) ─────────────────────────────

def register_enterprise_middleware(app, trusted_service_token: str | None = None) -> None:
    """Add OrgMiddleware to a FastAPI application instance."""
    app.add_middleware(OrgMiddleware, trusted_service_token=trusted_service_token)


# ─── Alembic migration (DDL reference) ───────────────────────────────────────

MIGRATION_SQL = """
-- Run via Alembic or psql.  Order matters (FK deps).

CREATE TABLE IF NOT EXISTS organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            VARCHAR(64) UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    domain          VARCHAR(255),
    primary_color   VARCHAR(32) NOT NULL DEFAULT '#7c3aed',
    secondary_color VARCHAR(32) NOT NULL DEFAULT '#4f46e5',
    logo_url        TEXT,
    agency_email    VARCHAR(255),
    agency_name     VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_organizations_slug   ON organizations(slug);
CREATE INDEX IF NOT EXISTS ix_organizations_domain ON organizations(domain);

CREATE TABLE IF NOT EXISTS org_memberships (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    org_id     UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role       VARCHAR(32) NOT NULL DEFAULT 'member'
);
CREATE INDEX IF NOT EXISTS ix_org_memberships_user_id ON org_memberships(user_id);
CREATE INDEX IF NOT EXISTS ix_org_memberships_org_id  ON org_memberships(org_id);
"""
