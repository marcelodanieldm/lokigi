"""
backend/app/enterprise/rbac_auth.py
========================================
FastAPI authorization layer: JWT decoding + RoleChecker dependency.

JWT contract
------------
Expected payload fields:
    {
      "sub":  "<user_id uuid>",          # mandatory
      "org":  "<org_id uuid>",           # set by auth service on login
      "role": "superadmin|network_manager|store_manager|store_staff",  # optional hint
      "exp":  <unix timestamp>,
      "iat":  <unix timestamp>
    }

The `role` claim is a hint for fast path; ground truth is always DB.
`org` is used only if request.state.org_id hasn't been resolved by OrgMiddleware.

Environment variables (add to .env)
------------------------------------
JWT_SECRET_KEY=<your-secret>   (HS256)  or omit to use RS256 with JWT_PUBLIC_KEY
JWT_ALGORITHM=HS256             default
JWT_AUDIENCE=lokigi-api         optional

Usage
-----
Protect a route by declaring the required roles:

    from app.enterprise.rbac_auth import RoleChecker

    @router.post("/bulk-publish")
    async def bulk_publish(
        _: None = Depends(RoleChecker(["superadmin", "network_manager"])),
        request: Request = ...,
        db: Session = Depends(get_db),
    ):
        ...

Require a specific permission (stricter):

    from app.enterprise.rbac_auth import PermissionChecker

    @router.get("/reports/consolidated")
    async def consolidated_report(
        _: None = Depends(PermissionChecker("reports.consolidated")),
        ...
    ):
        ...

Hierarchy shortcut (no DB query):

    from app.enterprise.rbac_auth import require_min_role
    from app.enterprise.rbac_models import RoleLevel

    @router.delete("/org/{org_id}")
    async def delete_org(
        _: None = Depends(require_min_role(RoleLevel.SUPER_ADMIN)),
        ...
    ):
        ...
"""
from __future__ import annotations

import logging
import uuid
from functools import lru_cache
from typing import Callable, Sequence

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import get_db
from app.enterprise.rbac_models import (
    RoleLevel,
    UserOrgRole,
    has_permission,
    user_can_access_location,
)

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _settings() -> Settings:
    return Settings()


# ─── JWT helpers ─────────────────────────────────────────────────────────────

class _JWTClaims:
    """Typed wrapper around the decoded JWT payload."""

    def __init__(self, payload: dict) -> None:
        self._p = payload

    @property
    def user_id(self) -> uuid.UUID:
        return uuid.UUID(str(self._p["sub"]))

    @property
    def org_id(self) -> uuid.UUID | None:
        raw = self._p.get("org")
        try:
            return uuid.UUID(str(raw)) if raw else None
        except ValueError:
            return None

    @property
    def role_hint(self) -> str | None:
        """Fast-path role hint; not trusted for authz — DB is authoritative."""
        return self._p.get("role")


def _decode_jwt(token: str) -> _JWTClaims:
    cfg = _settings()
    secret: str = getattr(cfg, "jwt_secret_key", "change-me-in-production")
    algorithm: str = getattr(cfg, "jwt_algorithm", "HS256")
    audience: str | None = getattr(cfg, "jwt_audience", None) or None

    decode_kwargs: dict = {
        "algorithms": [algorithm],
        "options": {"verify_exp": True},
    }
    if audience:
        decode_kwargs["audience"] = audience

    try:
        payload = jwt.decode(token, secret, **decode_kwargs)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _JWTClaims(payload)


def _extract_claims(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> _JWTClaims:
    """
    Resolve JWT claims from Bearer header.
    If no token is present and request.state already has user_id set by an
    upstream middleware (e.g. session-cookie auth), we construct minimal claims.
    """
    if credentials is not None:
        return _decode_jwt(credentials.credentials)

    # Fallback: upstream middleware set request.state.user_id
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return _JWTClaims({"sub": str(user_id)})

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _resolve_org_id(request: Request, claims: _JWTClaims) -> uuid.UUID | None:
    """OrgMiddleware wins; JWT org claim is the fallback."""
    middleware_org = getattr(request.state, "org_id", None)
    return middleware_org or claims.org_id


# ─── get_current_user_role ────────────────────────────────────────────────────

def get_current_user_role(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> UserOrgRole:
    """
    FastAPI dependency: resolves and returns the UserOrgRole for the
    authenticated user in the current org.  Raises 401/403 if not found.

    Attach to routes that need the full role object:

        @router.get("/dashboard")
        def dashboard(user_role: UserOrgRole = Depends(get_current_user_role)):
            ...
    """
    from sqlalchemy import select

    claims = _extract_claims(request, credentials)
    org_id = _resolve_org_id(request, claims)

    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No organization context",
        )

    stmt = select(UserOrgRole).where(
        UserOrgRole.user_id == claims.user_id,
        UserOrgRole.org_id == org_id,
    )
    user_role = db.scalars(stmt).first()

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization",
        )

    # Cache on request state for downstream dependencies (avoids double query)
    request.state.user_id = claims.user_id
    request.state.user_role = user_role
    return user_role


# ─── RoleChecker ─────────────────────────────────────────────────────────────

class RoleChecker:
    """
    FastAPI dependency that enforces role membership.

    Accepts a list of allowed role slugs.  The user must have AT LEAST ONE of
    the listed roles (or a higher-privilege role in the hierarchy).

    Example::

        @router.post("/invite")
        async def invite_user(
            _: None = Depends(RoleChecker(["superadmin"])),
            ...
        ):
            ...

    Hierarchy escalation: a SuperAdmin always passes a check for
    network_manager, store_manager, or store_staff — even if those roles are
    not listed explicitly.
    """

    def __init__(self, allowed_roles: Sequence[str]) -> None:
        self._min_level = min(
            RoleLevel.from_str(r) for r in allowed_roles
        )

    def __call__(
        self,
        user_role: UserOrgRole = Depends(get_current_user_role),
        db: Session = Depends(get_db),
    ) -> None:
        from sqlalchemy import select
        from app.enterprise.rbac_models import Role

        role_slug = db.scalars(
            select(Role.slug).where(Role.id == user_role.role_id)
        ).first() or "store_staff"

        actual_level = RoleLevel.from_str(role_slug)
        if actual_level < self._min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient role. Required: ≥{self._min_level.label()}, "
                    f"current: {actual_level.label()}"
                ),
            )


# ─── PermissionChecker ────────────────────────────────────────────────────────

class PermissionChecker:
    """
    FastAPI dependency that enforces a specific permission string.

    More granular than RoleChecker — checks the DB permissions table.

    Example::

        @router.get("/reports/export")
        async def export_report(
            _: None = Depends(PermissionChecker("reports.export")),
            ...
        ):
            ...
    """

    def __init__(self, permission_name: str) -> None:
        self._perm = permission_name

    def __call__(
        self,
        request: Request,
        user_role: UserOrgRole = Depends(get_current_user_role),
        db: Session = Depends(get_db),
    ) -> None:
        org_id = getattr(request.state, "org_id", None)
        user_id = user_role.user_id

        if not has_permission(user_id, self._perm, db, org_id=org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {self._perm}",
            )


# ─── LocationAccessChecker ───────────────────────────────────────────────────

class LocationAccessChecker:
    """
    FastAPI dependency that verifies the user can access a specific location.
    Inject `location_id` as a path parameter.

    Example::

        @router.get("/locations/{location_id}/reviews")
        async def get_reviews(
            location_id: str,
            _: None = Depends(LocationAccessChecker()),
            ...
        ):
            ...
    """

    def __call__(
        self,
        location_id: str,
        request: Request,
        user_role: UserOrgRole = Depends(get_current_user_role),
        db: Session = Depends(get_db),
    ) -> None:
        org_id = getattr(request.state, "org_id", None)
        if org_id is None:
            raise HTTPException(status_code=403, detail="No organization context")

        if not user_can_access_location(user_role.user_id, location_id, db, org_id=org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to location '{location_id}' is not authorized",
            )


# ─── require_min_role convenience ─────────────────────────────────────────────

def require_min_role(min_level: RoleLevel) -> Callable:
    """
    Shortcut for hierarchy-only checks without DB permission lookup.

    Usage::

        @router.delete("/org")
        async def nuke_org(
            _: None = Depends(require_min_role(RoleLevel.SUPER_ADMIN)),
        ):
            ...
    """
    checker = RoleChecker([min_level.name.lower().replace("_", "")])
    # Map back through slug
    slug_map = {
        RoleLevel.SUPER_ADMIN:     "superadmin",
        RoleLevel.NETWORK_MANAGER: "network_manager",
        RoleLevel.STORE_MANAGER:   "store_manager",
        RoleLevel.STORE_STAFF:     "store_staff",
    }
    return RoleChecker([slug_map[min_level]])
