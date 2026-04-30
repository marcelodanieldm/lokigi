"""
backend/app/enterprise/offboarding_router.py
=============================================
Enterprise Offboarding API — SuperAdmin-only endpoints to dismantle an org.

Endpoints
---------
GET    /enterprise/offboarding/{org_id}/impact
    Returns a full impact summary (users, locations, audit log count, domain).

POST   /enterprise/offboarding/{org_id}/hibernate
    Freeze the org (keep data, stop Celery tasks, no billing).

POST   /enterprise/offboarding/{org_id}/export/prepare
    Trigger background ZIP generation; returns a task token.

GET    /enterprise/offboarding/{org_id}/export/download
    Stream the pre-generated ZIP file as an attachment.

POST   /enterprise/offboarding/{org_id}/survey
    Save the partner exit-feedback survey.

POST   /enterprise/offboarding/{org_id}/confirm-deletion
    Final destructive action — requires org name confirmation.
    Sets status → pending_deletion, purges Celery schedule.

Security
--------
All endpoints require `RoleChecker(["superadmin"])`.
Confirm-deletion requires the requester to supply the exact org name as a
second-factor confirmation — prevents accidental triggers.
"""
from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.enterprise.audit_log import AuditAction, AuditService
from app.enterprise.multi_tenancy import Organization
from app.enterprise.offboarding_service import (
    ExportResult,
    OffboardingSurveyData,
    cleanup_export_temp,
    export_organization_data,
    get_impact_summary,
    hibernate_organization,
    save_offboarding_survey,
    schedule_deletion,
)
from app.enterprise.rbac_auth import RoleChecker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enterprise/offboarding", tags=["enterprise-offboarding"])
_require_superadmin = Depends(RoleChecker(["superadmin"]))

# In-memory store for generated export paths (keyed by org_id string).
# In a production multi-worker setup, replace with Redis or the DB.
_export_cache: dict[str, str] = {}


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class HibernatePayload(BaseModel):
    confirmed: bool = Field(..., description="Must be true to proceed")


class SurveyPayload(BaseModel):
    reason_primary:    str  = Field(..., max_length=120)
    score_support:     int  = Field(..., ge=1, le=10)
    score_scalability: int  = Field(..., ge=1, le=10)
    score_roi:         int  = Field(..., ge=1, le=10)
    open_feedback:     str  = Field("", max_length=4000)
    would_recommend:   bool = False


class DeletionConfirmPayload(BaseModel):
    org_name_confirmation: str = Field(
        ...,
        description="Must exactly match the organization's name",
        max_length=255,
    )
    survey_completed: bool = Field(
        default=False,
        description="True if the partner survey was already submitted",
    )

    @validator("org_name_confirmation")
    def no_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("org_name_confirmation must not be blank")
        return v.strip()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_org_or_404(org_id: uuid.UUID, db: Session) -> Organization:
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


def _require_active_or_hibernating(org: Organization) -> None:
    """Guard: only allow offboarding actions on orgs that haven't already been deleted."""
    current = getattr(org, "org_status", "active")
    if current == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization has already been cancelled",
        )


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/{org_id}/impact", dependencies=[_require_superadmin])
def get_offboarding_impact(
    org_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """
    Return a structured impact report: users, locations, audit entries, domain.
    Used to populate the "Are you sure?" warning screen.
    """
    try:
        summary = get_impact_summary(org_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return summary.to_dict()


@router.post("/{org_id}/hibernate", status_code=status.HTTP_200_OK, dependencies=[_require_superadmin])
def set_hibernation(
    org_id: uuid.UUID,
    payload: HibernatePayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """
    Freeze the org.  Data is preserved; Celery tasks are suspended; billing
    transitions to a maintenance plan (handled outside this service).
    """
    if not payload.confirmed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="confirmed must be true",
        )

    org = _get_org_or_404(org_id, db)
    _require_active_or_hibernating(org)

    try:
        hibernate_organization(org_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    AuditService.log(
        db,
        org_id=org_id,
        actor_id=None,   # TODO: pass current_user.id once auth dep is wired
        action=AuditAction.ORG_HIBERNATED,
        resource_type="organization",
        resource_id=str(org_id),
        details={"previous_status": getattr(org, "org_status", "active")},
        request=request,
    )

    return {
        "status": "hibernating",
        "message": "Organization frozen. Data preserved. Celery tasks suspended.",
        "org_id": str(org_id),
    }


@router.post(
    "/{org_id}/export/prepare",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[_require_superadmin],
)
def prepare_export(
    org_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """
    Kick off background ZIP generation.  Returns immediately with a poll URL.
    Once complete, the ZIP is available at GET .../export/download.
    """
    org = _get_org_or_404(org_id, db)

    def _run_export() -> None:
        # Use a new DB session for the background task
        from app.database import SessionLocal

        with SessionLocal() as bg_db:
            try:
                result: ExportResult = export_organization_data(org_id, bg_db)
                _export_cache[str(org_id)] = result.zip_path
                logger.info(
                    "Export ready for org %s: %d locations, %d rows, path=%s",
                    org_id, result.total_locations, result.total_rows, result.zip_path,
                )
            except Exception as exc:
                logger.error("Export failed for org %s: %s", org_id, exc, exc_info=True)
                _export_cache[str(org_id)] = "__error__"

    background_tasks.add_task(_run_export)

    AuditService.log(
        db,
        org_id=org_id,
        actor_id=None,
        action=AuditAction.ORG_DATA_EXPORTED,
        resource_type="organization",
        resource_id=str(org_id),
        details={"export_triggered": True},
        request=request,
    )

    return {
        "status": "preparing",
        "message": "Export job queued. Poll GET .../export/download to check readiness.",
        "org_id": str(org_id),
        "poll_url": f"/enterprise/offboarding/{org_id}/export/download",
    }


@router.get("/{org_id}/export/download", dependencies=[_require_superadmin])
def download_export(org_id: uuid.UUID, db: Session = Depends(get_db)) -> FileResponse:
    """
    Stream the master ZIP once the background job has finished.
    Returns 202 if still preparing, 500 if the job failed.
    """
    org = _get_org_or_404(org_id, db)
    zip_path = _export_cache.get(str(org_id))

    if zip_path is None:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Export is still being prepared. Try again in a few seconds.",
        )

    if zip_path == "__error__":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export job failed. Check server logs.",
        )

    if not Path(zip_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found. It may have been cleaned up. Re-trigger /export/prepare.",
        )

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=Path(zip_path).name,
        background=None,   # we DON'T auto-clean — caller handles via cleanup_export_temp()
    )


@router.post("/{org_id}/survey", status_code=status.HTTP_201_CREATED, dependencies=[_require_superadmin])
def submit_survey(
    org_id: uuid.UUID,
    payload: SurveyPayload,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """Save the qualitative partner exit survey."""
    _get_org_or_404(org_id, db)

    survey = OffboardingSurveyData(
        org_id=org_id,
        reason_primary=payload.reason_primary,
        score_support=payload.score_support,
        score_scalability=payload.score_scalability,
        score_roi=payload.score_roi,
        open_feedback=payload.open_feedback,
        would_recommend=payload.would_recommend,
    )
    save_offboarding_survey(survey, db)

    AuditService.log(
        db,
        org_id=org_id,
        actor_id=None,
        action=AuditAction.ORG_OFFBOARDING_SURVEY_SUBMITTED,
        resource_type="organization",
        resource_id=str(org_id),
        details={
            "reason": payload.reason_primary,
            "scores": {
                "support": payload.score_support,
                "scalability": payload.score_scalability,
                "roi": payload.score_roi,
            },
        },
        request=request,
    )

    return {"status": "saved", "org_id": str(org_id)}


@router.post(
    "/{org_id}/confirm-deletion",
    status_code=status.HTTP_200_OK,
    dependencies=[_require_superadmin],
)
def confirm_deletion(
    org_id: uuid.UUID,
    payload: DeletionConfirmPayload,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """
    Final destructive action.

    The requester must supply the exact organisation name as a confirmation
    token.  On success:
    - org.org_status → pending_deletion
    - org.deletion_scheduled_at → now()
    - All Celery Beat tasks for this org are removed
    - Audit log entry created
    - Export cache entry cleared

    The actual hard-delete (CASCADE) happens via a cron job at end of billing cycle.
    """
    org = _get_org_or_404(org_id, db)
    _require_active_or_hibernating(org)

    # ── Security: name confirmation ───────────────────────────────────────────
    if payload.org_name_confirmation != org.name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Organisation name confirmation does not match. "
                "Please type the exact name to proceed."
            ),
        )

    try:
        schedule_deletion(org_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    # Clean up export cache for this org
    _export_cache.pop(str(org_id), None)

    AuditService.log(
        db,
        org_id=org_id,
        actor_id=None,
        action=AuditAction.ORG_DELETION_CONFIRMED,
        resource_type="organization",
        resource_id=str(org_id),
        details={"confirmed_by_name": payload.org_name_confirmation},
        request=request,
    )

    return {
        "status": "pending_deletion",
        "message": (
            "Organisation scheduled for deletion. "
            "Access will remain until end of billing cycle. "
            "All Celery tasks have been removed."
        ),
        "org_id": str(org_id),
    }
