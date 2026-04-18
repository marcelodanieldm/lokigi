"""Google API grace period status endpoint.

Complements the cancellation endpoints with API status checks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Literal

from app.database import get_db
from app.models import User
from app.google_api_maintenance import GoogleAPIMaintenanceService

router = APIRouter(prefix="/api/cancellation", tags=["cancellation"])


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────────────────────────────────────


class GracePeriodStatusResponse(BaseModel):
    """Response for grace period status check."""
    status: Literal["active", "grace_period_active", "revoked", "expired", "no_connection"]
    user_id: str
    details: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/grace-period-status",
    response_model=GracePeriodStatusResponse,
    summary="Get Google API grace period status",
    description="Check if user's Google API permissions are in grace period after cancellation.",
)
async def get_grace_period_status(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get the current grace period status for the user's Google API permissions.
    
    Possible statuses:
    - **active**: Subscription is active, no grace period
    - **grace_period_active**: Subscription cancelled, access allowed until: [date]
    - **revoked**: Grace period expired, Google API permissions revoked
    - **expired**: Grace period has ended (should be revoked)
    - **no_connection**: User has no Google connection
    
    Returns:
    - status: Current state
    - user_id: User ID
    - details: Additional info (expires_at, days_remaining, etc)
    """
    try:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        grace_status = GoogleAPIMaintenanceService.get_grace_period_status(
            user_id=user.id,
            db=db,
        )
        
        return GracePeriodStatusResponse(
            status=grace_status.get("status", "no_connection"),
            user_id=str(user.id),
            details=grace_status,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking grace period status: {str(e)}",
        )
