"""app/rbac.py — Role-Based Access Control for multi-seat organizations.

Role hierarchy (highest to lowest):
    owner > admin > member > viewer

Permissions:
    manage_billing    — change plan, view invoices
    manage_members    — invite / remove / role-change members
    manage_locations  — connect / disconnect Google locations
    view_reports      — access analytics & PDF reports
    reply_reviews     — use auto-reply & manual reply tools
    view_analytics    — access CEO / growth dashboards

Usage in routes:
    @router.get("/some-route")
    def my_route(
        user_id: UUID = Query(...),
        org_id:  UUID = Query(...),
        _ctx:    RBACContext = Depends(require_permission("manage_members")),
        db:      Session    = Depends(get_db),
    ):
        # _ctx.member gives the resolved OrgMember row
        ...
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import OrgMember

logger = logging.getLogger(__name__)

# ── Permission map ────────────────────────────────────────────────────────────

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "owner": frozenset({
        "manage_billing", "manage_members", "manage_locations",
        "view_reports", "reply_reviews", "view_analytics",
    }),
    "admin": frozenset({
        "manage_members", "manage_locations",
        "view_reports", "reply_reviews", "view_analytics",
    }),
    "member": frozenset({
        "manage_locations", "view_reports", "reply_reviews",
    }),
    "viewer": frozenset({
        "view_reports",
    }),
}

# Ordered role tiers so we can compare "is role A higher than role B?"
ROLE_TIER: dict[str, int] = {
    "owner": 4,
    "admin": 3,
    "member": 2,
    "viewer": 1,
}


@dataclass
class RBACContext:
    """Resolved RBAC context injected into route handlers."""
    member: OrgMember
    user_id: UUID
    org_id: UUID

    @property
    def role(self) -> str:
        return self.member.role

    def has_permission(self, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, frozenset())

    def is_role_at_least(self, min_role: str) -> bool:
        return ROLE_TIER.get(self.role, 0) >= ROLE_TIER.get(min_role, 0)

    def can_assign_role(self, target_role: str) -> bool:
        """A member cannot assign a role equal to or higher than their own."""
        return ROLE_TIER.get(self.role, 0) > ROLE_TIER.get(target_role, 0)


# ── FastAPI dependency factory ────────────────────────────────────────────────

def require_permission(permission: str) -> Callable:
    """Return a FastAPI Depends that enforces the given permission.

    The caller's route must include:
        user_id: UUID = Query(...)
        org_id:  UUID = Query(...)

    Example:
        @router.patch("/members/{member_id}/role")
        def update_role(
            member_id: UUID,
            user_id: UUID = Query(...),
            org_id:  UUID = Query(...),
            _ctx: RBACContext = Depends(require_permission("manage_members")),
            db: Session = Depends(get_db),
        ): ...
    """

    def _dep(
        user_id: UUID = Query(...),
        org_id: UUID = Query(...),
        db: Session = Depends(get_db),
    ) -> RBACContext:
        # Single optimized query — uses composite index on (org_id, user_id)
        member = db.scalar(
            select(OrgMember).where(
                OrgMember.org_id == org_id,
                OrgMember.user_id == user_id,
                OrgMember.status == "active",
            )
        )
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "NOT_A_MEMBER",
                    "message": "No eres miembro activo de esta organización.",
                },
            )
        if permission not in ROLE_PERMISSIONS.get(member.role, frozenset()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Tu rol '{member.role}' no tiene el permiso '{permission}'.",
                    "required_permission": permission,
                    "your_role": member.role,
                },
            )
        return RBACContext(member=member, user_id=user_id, org_id=org_id)

    return Depends(_dep)


# ── Standalone helper (for use outside route context) ────────────────────────

def get_member_context(
    db: Session, user_id: UUID, org_id: UUID
) -> RBACContext | None:
    """Return an RBACContext or None if the user is not an active member."""
    member = db.scalar(
        select(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == user_id,
            OrgMember.status == "active",
        )
    )
    if member is None:
        return None
    return RBACContext(member=member, user_id=user_id, org_id=org_id)


def user_permissions(db: Session, user_id: UUID, org_id: UUID) -> frozenset[str]:
    """Return the permission set for a user in an org (empty if not a member)."""
    ctx = get_member_context(db, user_id, org_id)
    if ctx is None:
        return frozenset()
    return ROLE_PERMISSIONS.get(ctx.role, frozenset())
