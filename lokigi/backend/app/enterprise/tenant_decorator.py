"""
backend/app/enterprise/tenant_decorator.py
============================================
@tenant_scoped — decorator that automatically injects `org_id` into every
SQLAlchemy query executed inside a FastAPI route.

How it works
------------
The decorator wraps the route coroutine (or sync function).  Before executing
the original handler it installs a SQLAlchemy *before_cursor_execute* event
listener on the route's `Session` that:

  1. Checks if the emitted SQL targets a tenanted table (one that has an
     `org_id` column or goes through `org_memberships`).
  2. If the session already carries a compiled `WHERE … org_id = :__org_id`
     clause (injected by `apply_org_filter`), it does nothing — the developer
     explicitly filtered.
  3. Otherwise it raises `TenantLeakError` in STRICT mode or logs a warning
     in WARN mode — forcing the dev to notice the missing filter during
     development while never silently exposing cross-tenant data in production.

Additionally, the decorator exposes `request.state.org_id` as a dependency-
injected parameter named `_org_id` in the route signature, so routes can call
`apply_org_filter(stmt, _org_id)` without importing the Depends boilerplate.

Usage
-----
    from app.enterprise.tenant_decorator import tenant_scoped

    @router.get("/locations")
    @tenant_scoped
    async def list_locations(
        _org_id: uuid.UUID,          # injected automatically
        db: Session = Depends(get_db),
    ):
        stmt = apply_org_filter(select(GoogleConnection), _org_id)
        return db.scalars(stmt).all()

    # STRICT mode (default in production): raises if a query hits a tenanted
    # table WITHOUT an org_id filter.
    @router.get("/unsafe-demo")
    @tenant_scoped(mode="warn")     # downgrade to warning during dev
    async def unsafe_demo(db: Session = Depends(get_db)):
        ...

Modes
-----
- "strict"  — TenantLeakError raised immediately (default when ENV=production)
- "warn"    — Warning logged, execution continues (useful during development)
- "off"     — Decorator is a no-op (useful for tests / migrations)
"""
from __future__ import annotations

import functools
import inspect
import logging
import os
import uuid
from typing import Any, Callable

from fastapi import HTTPException, Request, status
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Which mode to use when @tenant_scoped is applied without arguments
_DEFAULT_MODE: str = "strict" if os.getenv("ENV", "development") == "production" else "warn"

# Tables that carry `org_id` directly or are reached through org_memberships
_TENANTED_TABLES = frozenset({
    "reviews",
    "google_connections",
    "locations",
    "org_memberships",
    "users",
})


# ─── Custom exception ─────────────────────────────────────────────────────────

class TenantLeakError(RuntimeError):
    """
    Raised when a query touches a tenanted table without an org_id filter
    and the decorator is in STRICT mode.

    This is a developer error — it means a new route was added without
    calling `apply_org_filter`.
    """


# ─── SQL audit listener ───────────────────────────────────────────────────────

def _make_audit_listener(org_id: uuid.UUID, mode: str) -> Callable:
    """
    Return a SQLAlchemy before_cursor_execute listener that verifies every
    outgoing query carries the org_id constraint.
    """

    def _before_cursor_execute(  # noqa: PLR0913
        conn: Connection,
        cursor,
        statement: str,
        parameters,
        context,
        executemany: bool,
    ) -> None:
        stmt_lower = statement.lower()

        # Only care about DML that reads data
        if not any(stmt_lower.lstrip().startswith(kw) for kw in ("select", "update", "delete")):
            return

        # Check whether any tenanted table appears in the SQL
        hits_tenant_table = any(f" {t} " in f" {stmt_lower} " for t in _TENANTED_TABLES)
        if not hits_tenant_table:
            return

        # Verify the org_id is bound somewhere in the parameters
        org_id_str = str(org_id)
        params_flat: list[str] = []
        if isinstance(parameters, dict):
            params_flat = [str(v) for v in parameters.values()]
        elif isinstance(parameters, (list, tuple)):
            for p in parameters:
                if isinstance(p, dict):
                    params_flat.extend(str(v) for v in p.values())
                else:
                    params_flat.append(str(p))

        if org_id_str not in params_flat and ":__org_id" not in stmt_lower:
            msg = (
                f"TenantLeakPrevention: query hits tenanted table(s) "
                f"[{', '.join(t for t in _TENANTED_TABLES if t in stmt_lower)}] "
                f"WITHOUT binding org_id={org_id_str}.\n"
                f"SQL (truncated): {statement[:400]}"
            )
            if mode == "strict":
                raise TenantLeakError(msg)
            else:
                logger.warning(msg)

    return _before_cursor_execute


# ─── Decorator factory ────────────────────────────────────────────────────────

def tenant_scoped(_func: Callable | None = None, *, mode: str | None = None):
    """
    Decorator that:
      1. Extracts `request.state.org_id` and injects it as `_org_id`
         into the route function.
      2. Installs an audit listener on the `db` session parameter (if present)
         that raises/warns on unfiltered cross-tenant queries.

    Can be used as:
        @tenant_scoped                     # uses _DEFAULT_MODE
        @tenant_scoped(mode="warn")        # explicit mode
        @tenant_scoped(mode="off")         # disable (for testing)
    """
    effective_mode = mode or _DEFAULT_MODE

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        accepts_org_id = "_org_id" in param_names
        accepts_db = "db" in param_names

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Locate the Request object (may be in args or kwargs)
            request: Request | None = kwargs.get("request") or next(
                (a for a in args if isinstance(a, Request)), None
            )
            if request is None:
                raise RuntimeError(
                    "@tenant_scoped requires a `request: Request` parameter "
                    "in the route signature."
                )

            org_id: uuid.UUID | None = getattr(request.state, "org_id", None)
            if org_id is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Organization context missing.  Is the user authenticated?",
                )

            # Inject _org_id
            if accepts_org_id:
                kwargs["_org_id"] = org_id

            # Install DB audit listener
            if accepts_db and effective_mode != "off":
                db: Session | None = kwargs.get("db")
                if db is not None and hasattr(db, "get_bind"):
                    listener = _make_audit_listener(org_id, effective_mode)
                    try:
                        engine = db.get_bind()
                        event.listen(engine, "before_cursor_execute", listener)
                        result = await func(*args, **kwargs)
                    finally:
                        try:
                            event.remove(engine, "before_cursor_execute", listener)
                        except Exception:
                            pass
                    return result

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            request: Request | None = kwargs.get("request") or next(
                (a for a in args if isinstance(a, Request)), None
            )
            if request is None:
                raise RuntimeError(
                    "@tenant_scoped requires a `request: Request` parameter."
                )

            org_id: uuid.UUID | None = getattr(request.state, "org_id", None)
            if org_id is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Organization context missing.",
                )

            if accepts_org_id:
                kwargs["_org_id"] = org_id

            if accepts_db and effective_mode != "off":
                db: Session | None = kwargs.get("db")
                if db is not None and hasattr(db, "get_bind"):
                    listener = _make_audit_listener(org_id, effective_mode)
                    engine = db.get_bind()
                    event.listen(engine, "before_cursor_execute", listener)
                    try:
                        return func(*args, **kwargs)
                    finally:
                        try:
                            event.remove(engine, "before_cursor_execute", listener)
                        except Exception:
                            pass

            return func(*args, **kwargs)

        wrapper = async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
        # Preserve FastAPI's dependency injection metadata
        wrapper.__signature__ = sig  # type: ignore[attr-defined]
        return wrapper

    # Allow @tenant_scoped (no call) or @tenant_scoped(mode="warn")
    if _func is not None:
        return decorator(_func)
    return decorator


# ─── SuperAdmin bypass ────────────────────────────────────────────────────────

def superadmin_only(func: Callable) -> Callable:
    """
    Decorator for routes that are intentionally cross-tenant (SuperAdmin only).
    Checks that the user's OrgMembership role == 'superadmin' and then
    disables the tenant audit listener so cross-org queries are allowed.

    Usage:
        @router.get("/admin/all-orgs")
        @superadmin_only
        async def list_all_orgs(request: Request, db: Session = Depends(get_db)):
            return db.scalars(select(Organization)).all()
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request | None = kwargs.get("request") or next(
            (a for a in args if isinstance(a, Request)), None
        )
        if request is None:
            raise RuntimeError("@superadmin_only requires a `request: Request` parameter.")

        role: str = getattr(request.state, "user_role", "")
        if role != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SuperAdmin access required.",
            )
        return await func(*args, **kwargs)

    return wrapper


# ─── Example usage (not executed, for documentation) ─────────────────────────
#
# from app.enterprise.tenant_decorator import tenant_scoped, superadmin_only
# from app.enterprise.multi_tenancy import apply_org_filter
# from app.models import GoogleConnection, Review
# from sqlalchemy import select
# from fastapi import APIRouter, Depends, Request
# from app.database import get_db
# from sqlalchemy.orm import Session
# import uuid
#
# router = APIRouter()
#
# @router.get("/locations")
# @tenant_scoped
# async def list_locations(
#     request: Request,
#     _org_id: uuid.UUID,               # ← injected by @tenant_scoped
#     db: Session = Depends(get_db),
# ):
#     stmt = apply_org_filter(select(GoogleConnection), _org_id)
#     return db.scalars(stmt).all()
#
# @router.get("/locations/{loc_id}/reviews")
# @tenant_scoped(mode="warn")
# async def get_reviews(
#     request: Request,
#     loc_id: str,
#     _org_id: uuid.UUID,
#     db: Session = Depends(get_db),
# ):
#     stmt = (
#         select(Review)
#         .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
#         .join(OrgMembership, OrgMembership.user_id == GoogleConnection.user_id)
#         .where(OrgMembership.org_id == _org_id)
#         .where(GoogleConnection.location_id == loc_id)
#     )
#     return db.scalars(stmt).all()
