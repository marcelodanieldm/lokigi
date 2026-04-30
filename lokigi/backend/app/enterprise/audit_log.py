"""
backend/app/enterprise/audit_log.py
========================================
Activity Audit Log — tracks every consequential action inside an org.

Records WHO did WHAT to WHICH RESOURCE and WHEN, with enough context for:
  - Compliance audits ("who approved that reply?")
  - Crisis post-mortems ("who silenced the alert?")
  - Fraud detection ("why did someone export all reviews at 3 AM?")

Design
------
- Immutable append-only table (no UPDATE/DELETE on audit rows — ever).
- Actions are string enums stored as TEXT for easy extensibility.
- `details` is a JSONB field for action-specific payload without schema churn.
- The `AuditService` exposes a single write method and paginated read method.
- FastAPI router exposed at GET /enterprise/audit-logs (superadmin/network_manager only).

Usage
-----
    from app.enterprise.audit_log import AuditService, AuditAction

    # In a route that approves a reply:
    await AuditService.log(
        db,
        org_id=org.id,
        actor_id=current_user.id,
        action=AuditAction.REVIEW_REPLY_APPROVED,
        resource_type="review",
        resource_id=str(review.id),
        details={"location_id": gc.location_id, "reply_snippet": reply[:80]},
        request=request,
    )
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database import Base, get_db
from app.enterprise.rbac_auth import RoleChecker


# ─── Action enum ──────────────────────────────────────────────────────────────

class AuditAction(str, enum.Enum):
    # User management
    USER_INVITED             = "user.invited"
    USER_REMOVED             = "user.removed"
    USER_ROLE_CHANGED        = "user.role_changed"
    USER_LOCATION_GRANTED    = "user.location_granted"
    USER_LOCATION_REVOKED    = "user.location_revoked"

    # Review actions
    REVIEW_REPLY_APPROVED    = "review.reply.approved"
    REVIEW_REPLY_REJECTED    = "review.reply.rejected"
    REVIEW_REPLY_SENT        = "review.reply.sent"
    REVIEW_REPLY_BULK_SENT   = "review.reply.bulk_sent"

    # Crisis actions
    CRISIS_ALERT_RAISED      = "crisis.alert.raised"
    CRISIS_ALERT_ESCALATED   = "crisis.alert.escalated"
    CRISIS_ALERT_SILENCED    = "crisis.alert.silenced"
    CRISIS_ALERT_RESOLVED    = "crisis.alert.resolved"

    # Reports
    REPORT_EXPORTED          = "report.exported"
    REPORT_CONSOLIDATED_VIEW = "report.consolidated.viewed"

    # Org settings
    ORG_WHITE_LABEL_UPDATED  = "org.white_label.updated"
    ORG_BILLING_UPDATED      = "org.billing.updated"
    ORG_SETTINGS_UPDATED     = "org.settings.updated"

    # Bulk operations
    BULK_PUBLISH_TRIGGERED   = "bulk.publish.triggered"
    BULK_REPLY_TRIGGERED     = "bulk.reply.triggered"

    # Auth
    LOGIN_SUCCESS            = "auth.login.success"
    LOGIN_FAILED             = "auth.login.failed"
    TOKEN_REFRESHED          = "auth.token.refreshed"

    # Org lifecycle — onboarding
    ORG_CREATED              = "org.created"
    ORG_SMTP_CONFIGURED      = "org.smtp.configured"

    # Org lifecycle — offboarding
    ORG_HIBERNATED                  = "org.hibernated"
    ORG_DATA_EXPORTED               = "org.data.exported"
    ORG_DELETION_CONFIRMED          = "org.deletion.confirmed"
    ORG_OFFBOARDING_SURVEY_SUBMITTED = "org.offboarding.survey.submitted"


# ─── Model ────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    """
    Immutable activity log record.

    IMPORTANT: Never UPDATE or DELETE rows in this table.
    Enforce via Postgres row-level security policy in production:
      CREATE POLICY audit_immutable ON audit_logs FOR UPDATE USING (false);
      CREATE POLICY audit_immutable_del ON audit_logs FOR DELETE USING (false);
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_org_id_created_at", "org_id", "created_at"),
        Index("ix_audit_logs_actor_id",          "actor_id"),
        Index("ix_audit_logs_action",             "action"),
        Index("ix_audit_logs_resource",           "resource_type", "resource_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # system-generated events have no actor
    )
    actor_role: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # snapshot of role at time of action — don't re-query for audit

    action: Mapped[str] = mapped_column(String(128), nullable=False)

    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Network context — helps post-mortems
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)   # IPv4/IPv6
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()", index=True
    )


# ─── AuditService ─────────────────────────────────────────────────────────────

class AuditService:
    """Static service — no instance needed."""

    @staticmethod
    def log(
        db: Session,
        *,
        org_id: uuid.UUID,
        action: AuditAction | str,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        request: Request | None = None,
    ) -> AuditLog:
        """
        Write one audit event.  Never raises — swallows exceptions so an audit
        failure never breaks the main request path.

        Parameters
        ----------
        db:            Active session (the caller's — we flush but don't commit).
        org_id:        Organization context.
        action:        AuditAction enum value or raw string.
        actor_id:      UUID of the user performing the action (None = system).
        actor_role:    Snapshot of actor's role slug at time of action.
        resource_type: "review" | "location" | "user" | "org" | etc.
        resource_id:   String PK of the affected resource.
        details:       Extra JSON payload.
        request:       If provided, IP address and User-Agent are extracted.
        """
        try:
            ip: str | None = None
            ua: str | None = None
            if request is not None:
                # X-Forwarded-For set by load balancer / proxy
                ip = (
                    request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                    or request.client.host
                    if request.client
                    else None
                )
                ua = request.headers.get("User-Agent", "")[:512]

            entry = AuditLog(
                org_id=org_id,
                actor_id=actor_id,
                actor_role=actor_role,
                action=str(action),
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip,
                user_agent=ua,
            )
            db.add(entry)
            db.flush()   # assign PK; caller controls commit
            return entry
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "AuditService.log failed silently for action=%s org=%s",
                action, org_id,
            )
            # Return a detached stub so callers don't break on .id access
            return AuditLog(
                id=uuid.uuid4(),
                org_id=org_id,
                action=str(action),
                created_at=datetime.utcnow(),
            )

    @staticmethod
    def query(
        db: Session,
        *,
        org_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """
        Return paginated audit log entries for an org, newest first.

        All filter parameters are optional AND-combined.
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.org_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .limit(min(limit, 200))
            .offset(offset)
        )
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type is not None:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            stmt = stmt.where(AuditLog.resource_id == resource_id)

        return list(db.scalars(stmt).all())


# ─── FastAPI router ───────────────────────────────────────────────────────────

def make_audit_router() -> APIRouter:
    """
    Returns a FastAPI router for the audit log endpoint.

    Mount in main.py:
        from app.enterprise.audit_log import make_audit_router
        app.include_router(make_audit_router())
    """
    router = APIRouter(prefix="/enterprise/audit-logs", tags=["enterprise-audit"])

    @router.get("")
    def list_audit_logs(
        request: Request,
        actor_id: uuid.UUID | None = Query(None),
        action: str | None = Query(None),
        resource_type: str | None = Query(None),
        resource_id: str | None = Query(None),
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        _: None = Depends(RoleChecker(["superadmin", "network_manager"])),
        db: Session = Depends(get_db),
    ) -> list[dict]:
        org_id = getattr(request.state, "org_id", None)
        if org_id is None:
            from fastapi import HTTPException
            raise HTTPException(403, "No organization context")

        entries = AuditService.query(
            db,
            org_id=org_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
            offset=offset,
        )
        return [
            {
                "id":            str(e.id),
                "actor_id":      str(e.actor_id) if e.actor_id else None,
                "actor_role":    e.actor_role,
                "action":        e.action,
                "resource_type": e.resource_type,
                "resource_id":   e.resource_id,
                "details":       e.details,
                "ip_address":    e.ip_address,
                "created_at":    e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]

    return router
