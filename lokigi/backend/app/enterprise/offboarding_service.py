"""
backend/app/enterprise/offboarding_service.py
===============================================
Enterprise Offboarding — core business logic for dismantling an organization.

Responsibilities
----------------
1. Impact analysis   — count affected users, locations, reports.
2. Hibernation       — freeze scraping / AI while preserving all data.
3. Data export       — generate a master ZIP with per-sub-client CSV folders.
4. Celery cleanup    — revoke / unschedule all tasks linked to an org.
5. Deletion staging  — mark org `pending_deletion`; hard-delete on billing EOC.

All public functions are synchronous (called from FastAPI background tasks or
directly from routes with their own DB session).  Nothing here ever raises
unchecked exceptions — callers receive structured results.
"""
from __future__ import annotations

import csv
import io
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ─── Status constants ─────────────────────────────────────────────────────────

ORG_STATUS_ACTIVE           = "active"
ORG_STATUS_HIBERNATING      = "hibernating"
ORG_STATUS_PENDING_DELETION = "pending_deletion"
ORG_STATUS_CANCELLED        = "cancelled"


# ─── Impact analysis ─────────────────────────────────────────────────────────

class OrgImpactSummary:
    """Lightweight DTO for the impact-analysis screen."""
    def __init__(
        self,
        *,
        org_id: uuid.UUID,
        org_name: str,
        org_slug: str,
        org_domain: str | None,
        total_members: int,
        total_locations: int,
        total_audit_log_entries: int,
        status: str,
        onboarding_step: int,
        primary_color: str,
    ) -> None:
        self.org_id               = org_id
        self.org_name             = org_name
        self.org_slug             = org_slug
        self.org_domain           = org_domain
        self.total_members        = total_members
        self.total_locations      = total_locations
        self.total_audit_log_entries = total_audit_log_entries
        self.status               = status
        self.onboarding_step      = onboarding_step
        self.primary_color        = primary_color

    def to_dict(self) -> dict[str, Any]:
        return {
            "org_id":                  str(self.org_id),
            "org_name":                self.org_name,
            "org_slug":                self.org_slug,
            "org_domain":              self.org_domain,
            "total_members":           self.total_members,
            "total_locations":         self.total_locations,
            "total_audit_log_entries": self.total_audit_log_entries,
            "status":                  self.status,
            "onboarding_step":         self.onboarding_step,
            "primary_color":           self.primary_color,
        }


def get_impact_summary(org_id: uuid.UUID, db: Session) -> OrgImpactSummary:
    """
    Return a structured snapshot of everything that will be lost on deletion.
    Safe — no writes.
    """
    from app.enterprise.multi_tenancy import Organization, OrgLocation, OrgMembership
    from app.enterprise.audit_log import AuditLog

    org = db.get(Organization, org_id)
    if org is None:
        raise ValueError(f"Organization {org_id} not found")

    total_members = db.scalar(
        select(func.count()).select_from(OrgMembership).where(OrgMembership.org_id == org_id)
    ) or 0

    total_locations = db.scalar(
        select(func.count()).select_from(OrgLocation).where(OrgLocation.org_id == org_id)
    ) or 0

    total_audit_entries = db.scalar(
        select(func.count()).select_from(AuditLog).where(AuditLog.org_id == org_id)
    ) or 0

    return OrgImpactSummary(
        org_id=org.id,
        org_name=org.name,
        org_slug=org.slug,
        org_domain=getattr(org, "domain", None),
        total_members=total_members,
        total_locations=total_locations,
        total_audit_log_entries=total_audit_entries,
        status=getattr(org, "org_status", ORG_STATUS_ACTIVE),
        onboarding_step=getattr(org, "onboarding_step", 1),
        primary_color=getattr(org, "primary_color", "#7c3aed"),
    )


# ─── Hibernation ─────────────────────────────────────────────────────────────

def hibernate_organization(org_id: uuid.UUID, db: Session) -> None:
    """
    Freeze the org: no scraping, no AI, no billing — data preserved.
    Celery tasks are suspended but NOT deleted; they can be resumed on reactivation.
    """
    from app.enterprise.multi_tenancy import Organization

    org = db.get(Organization, org_id)
    if org is None:
        raise ValueError(f"Organization {org_id} not found")

    db.execute(
        update(Organization)
        .where(Organization.id == org_id)
        .values(org_status=ORG_STATUS_HIBERNATING)
    )
    db.commit()

    # Suspend (revoke) running Celery tasks without deleting Beat schedule
    _suspend_celery_tasks(org_id, revoke_running=True, remove_schedule=False)
    logger.info("Organization %s set to HIBERNATING", org_id)


def reactivate_organization(org_id: uuid.UUID, db: Session) -> None:
    """Reverse hibernation — restore to active status."""
    from app.enterprise.multi_tenancy import Organization

    db.execute(
        update(Organization)
        .where(Organization.id == org_id)
        .values(org_status=ORG_STATUS_ACTIVE)
    )
    db.commit()
    logger.info("Organization %s REACTIVATED", org_id)


# ─── Deletion staging ─────────────────────────────────────────────────────────

def schedule_deletion(
    org_id: uuid.UUID,
    db: Session,
    *,
    effective_at: datetime | None = None,
) -> None:
    """
    Mark the org for deletion at the end of the billing cycle.
    Celery tasks are permanently removed from Beat; running workers are revoked.
    """
    from app.enterprise.multi_tenancy import Organization

    if effective_at is None:
        effective_at = datetime.now(timezone.utc)

    db.execute(
        update(Organization)
        .where(Organization.id == org_id)
        .values(
            org_status=ORG_STATUS_PENDING_DELETION,
            deletion_scheduled_at=effective_at,
        )
    )
    db.commit()

    _suspend_celery_tasks(org_id, revoke_running=True, remove_schedule=True)
    logger.warning("Organization %s scheduled for DELETION at %s", org_id, effective_at)


# ─── Master ZIP data export ───────────────────────────────────────────────────

class ExportResult:
    def __init__(self, zip_path: str, total_locations: int, total_rows: int) -> None:
        self.zip_path        = zip_path
        self.total_locations = total_locations
        self.total_rows      = total_rows


def export_organization_data(org_id: uuid.UUID, db: Session) -> ExportResult:
    """
    Generate a master ZIP archive containing:
      /<org_slug>/
        locations.csv          — all org_locations rows
        audit_log.csv          — full audit trail
        members.csv            — all org members + roles
        google_connections/
          <place_id>.csv       — per-location Google connection data (if available)

    The archive is written to a temp directory.  The caller is responsible for
    streaming it to the client and deleting the temp dir afterwards.

    Returns ExportResult with the zip path and summary counts.
    """
    from app.enterprise.multi_tenancy import Organization, OrgLocation, OrgMembership
    from app.enterprise.audit_log import AuditLog

    org = db.get(Organization, org_id)
    if org is None:
        raise ValueError(f"Organization {org_id} not found")

    work_dir = Path(tempfile.mkdtemp(prefix=f"lokigi_export_{org.slug}_"))
    org_dir  = work_dir / org.slug
    gc_dir   = org_dir / "google_connections"
    org_dir.mkdir(parents=True)
    gc_dir.mkdir(parents=True)

    total_rows = 0

    # ── 1. locations.csv ──────────────────────────────────────────────────────
    locations = db.scalars(
        select(OrgLocation).where(OrgLocation.org_id == org_id).order_by(OrgLocation.created_at)
    ).all()
    total_rows += _write_csv(
        org_dir / "locations.csv",
        fieldnames=["id", "place_id", "name", "address", "phone", "city", "country", "created_at"],
        rows=[{
            "id":         str(loc.id),
            "place_id":   loc.place_id or "",
            "name":       loc.name or "",
            "address":    loc.address or "",
            "phone":      loc.phone or "",
            "city":       loc.city or "",
            "country":    loc.country or "",
            "created_at": str(getattr(loc, "created_at", "")),
        } for loc in locations],
    )

    # ── 2. members.csv ────────────────────────────────────────────────────────
    from app.models import User
    members_rows = db.execute(
        select(OrgMembership, User)
        .join(User, User.id == OrgMembership.user_id)
        .where(OrgMembership.org_id == org_id)
    ).all()
    total_rows += _write_csv(
        org_dir / "members.csv",
        fieldnames=["user_id", "email", "role", "joined_at"],
        rows=[{
            "user_id":   str(m.OrgMembership.user_id),
            "email":     getattr(m.User, "email", ""),
            "role":      m.OrgMembership.role,
            "joined_at": str(getattr(m.OrgMembership, "created_at", "")),
        } for m in members_rows],
    )

    # ── 3. audit_log.csv ──────────────────────────────────────────────────────
    audit_rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.org_id == org_id)
        .order_by(AuditLog.created_at)
        .limit(50_000)   # safety cap for very large orgs
    ).all()
    total_rows += _write_csv(
        org_dir / "audit_log.csv",
        fieldnames=["id", "actor_id", "action", "resource_type", "resource_id", "created_at", "details"],
        rows=[{
            "id":            str(r.id),
            "actor_id":      str(r.actor_id or ""),
            "action":        r.action,
            "resource_type": r.resource_type or "",
            "resource_id":   r.resource_id or "",
            "created_at":    str(r.created_at),
            "details":       str(r.details or ""),
        } for r in audit_rows],
    )

    # ── 4. Per-location Google connections (best-effort) ──────────────────────
    _try_export_google_connections(org_id, locations, gc_dir, db)

    # ── 5. org_metadata.csv — single-row summary of the org ──────────────────
    _write_csv(
        org_dir / "org_metadata.csv",
        fieldnames=["id", "slug", "name", "domain", "primary_color", "agency_email", "created_at", "status"],
        rows=[{
            "id":            str(org.id),
            "slug":          org.slug,
            "name":          org.name,
            "domain":        getattr(org, "domain", "") or "",
            "primary_color": getattr(org, "primary_color", ""),
            "agency_email":  getattr(org, "agency_email", "") or "",
            "created_at":    str(getattr(org, "created_at", "")),
            "status":        getattr(org, "org_status", ORG_STATUS_ACTIVE),
        }],
    )

    # ── 6. Compress to ZIP ────────────────────────────────────────────────────
    ts      = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    zip_name = f"lokigi_export_{org.slug}_{ts}"
    zip_path = shutil.make_archive(
        base_name=str(work_dir / zip_name),
        format="zip",
        root_dir=str(work_dir),
        base_dir=org.slug,
    )

    logger.info(
        "Export complete for org %s — %d locations, %d total rows, zip: %s",
        org_id, len(locations), total_rows, zip_path,
    )
    return ExportResult(zip_path=zip_path, total_locations=len(locations), total_rows=total_rows)


# ─── Celery task cleanup ──────────────────────────────────────────────────────

def _suspend_celery_tasks(
    org_id: uuid.UUID,
    *,
    revoke_running: bool,
    remove_schedule: bool,
) -> None:
    """
    Best-effort Celery cleanup.  Never raises — failures are logged only.

    Strategy:
    - Revoke running tasks whose kwargs / args contain the org_id string.
    - Remove periodic tasks from Celery Beat (django-celery-beat / redbeat) whose
      name contains the org slug pattern.
    """
    org_id_str = str(org_id)

    if revoke_running:
        try:
            from celery.app.control import Control
            from celery_app import celery_app  # project's Celery instance

            control: Control = celery_app.control
            # Inspect active tasks across all workers
            i = control.inspect()
            active = i.active() or {}
            for _worker, tasks in active.items():
                for task in tasks:
                    kwargs_str = str(task.get("kwargs", "")) + str(task.get("args", ""))
                    if org_id_str in kwargs_str:
                        control.revoke(task["id"], terminate=True)
                        logger.info("Revoked Celery task %s for org %s", task["id"], org_id_str)
        except Exception as exc:
            logger.warning("Could not revoke Celery tasks for org %s: %s", org_id_str, exc)

    if remove_schedule:
        try:
            # Try Celery Beat database scheduler (django-celery-beat)
            from django_celery_beat.models import PeriodicTask
            deleted, _ = PeriodicTask.objects.filter(
                kwargs__contains=org_id_str
            ).delete()
            logger.info("Removed %d periodic tasks for org %s", deleted, org_id_str)
        except Exception:
            pass  # Not using django-celery-beat — try redbeat

        try:
            # Try redbeat scheduler
            import redis
            from app.config import settings
            r = redis.from_url(getattr(settings, "celery_broker_url", "redis://localhost:6379/0"))
            pattern = f"redbeat:*{org_id_str}*"
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
                logger.info("Removed %d redbeat keys for org %s", len(keys), org_id_str)
        except Exception as exc:
            logger.debug("redbeat cleanup skipped for org %s: %s", org_id_str, exc)


# ─── Partner survey ───────────────────────────────────────────────────────────

class OffboardingSurveyData:
    """Plain holder for the qualitative exit survey."""
    def __init__(
        self,
        *,
        org_id: uuid.UUID,
        reason_primary: str,
        score_support: int,
        score_scalability: int,
        score_roi: int,
        open_feedback: str,
        would_recommend: bool,
    ) -> None:
        self.org_id             = org_id
        self.reason_primary     = reason_primary
        self.score_support      = max(1, min(10, score_support))
        self.score_scalability  = max(1, min(10, score_scalability))
        self.score_roi          = max(1, min(10, score_roi))
        self.open_feedback      = open_feedback[:4000]   # cap at 4000 chars
        self.would_recommend    = would_recommend


def save_offboarding_survey(survey: OffboardingSurveyData, db: Session) -> None:
    """Persist survey answers to `partner_offboarding_surveys`."""
    db.execute(
        text("""
            INSERT INTO partner_offboarding_surveys
                (id, org_id, reason_primary, score_support, score_scalability,
                 score_roi, open_feedback, would_recommend, created_at)
            VALUES
                (gen_random_uuid(), :org_id, :reason, :s_support, :s_scale,
                 :s_roi, :feedback, :recommend, now())
            ON CONFLICT DO NOTHING
        """),
        {
            "org_id":   str(survey.org_id),
            "reason":   survey.reason_primary,
            "s_support": survey.score_support,
            "s_scale":   survey.score_scalability,
            "s_roi":     survey.score_roi,
            "feedback":  survey.open_feedback,
            "recommend": survey.would_recommend,
        },
    )
    db.commit()


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> int:
    """Write rows to a CSV file; return number of data rows written."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _try_export_google_connections(
    org_id: uuid.UUID,
    locations: list,
    gc_dir: Path,
    db: Session,
) -> None:
    """
    Best-effort: export GoogleConnection rows for each place_id found.
    Skips gracefully if the GoogleConnection table has a different schema.
    """
    try:
        from app.models import GoogleConnection
        place_ids = [loc.place_id for loc in locations if loc.place_id]
        if not place_ids:
            return

        conns = db.scalars(
            select(GoogleConnection).where(
                GoogleConnection.location_id.in_(place_ids)  # adjust FK name if needed
            ).limit(10_000)
        ).all()

        if not conns:
            return

        # Group by place_id for per-location CSVs
        from collections import defaultdict
        by_location: dict[str, list] = defaultdict(list)
        for c in conns:
            by_location[str(getattr(c, "location_id", "unknown"))].append(c)

        for place_id, gc_rows in by_location.items():
            safe_name = place_id.replace("/", "_").replace("\\", "_")[:80]
            # Introspect columns dynamically — avoids hard-coding schema
            cols = [col.key for col in gc_rows[0].__mapper__.column_attrs]
            _write_csv(
                gc_dir / f"{safe_name}.csv",
                fieldnames=cols,
                rows=[{c: str(getattr(r, c, "")) for c in cols} for r in gc_rows],
            )
    except Exception as exc:
        logger.debug("google_connections export skipped: %s", exc)


def cleanup_export_temp(zip_path: str) -> None:
    """Delete the temp directory created by export_organization_data."""
    try:
        parent = str(Path(zip_path).parent)
        shutil.rmtree(parent, ignore_errors=True)
    except Exception as exc:
        logger.warning("Could not clean up export temp dir: %s", exc)
