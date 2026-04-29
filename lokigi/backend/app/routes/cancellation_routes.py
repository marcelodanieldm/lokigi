"""Cancellation & retention API endpoints.

POST   /api/cancellation/impact-data      - Get impact data for modal
POST   /api/cancellation/initiate          - Start cancellation flow
POST   /api/cancellation/plan-pausa        - Downgrade to Plan Pausa
POST   /api/cancellation/confirm           - Confirm final cancellation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
import csv
import io
from datetime import datetime

from app.database import get_db
from app.models import GoogleConnection, Review, User
from app.cancellation_service import CancellationService

router = APIRouter(prefix="/api/cancellation", tags=["cancellation"])


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────────────────────────────────────


class ImpactDataResponse(BaseModel):
    """Impact data for cancellation modal."""
    user_id: str
    hours_saved_this_month: float
    responses_approved_this_month: int
    impact_message: str
    total_reviews_processed: int
    total_approved_responses: int
    approval_rate: float
    days_subscribed: int
    current_plan: str
    is_high_value: bool
    plan_price_monthly: float


class DownsellOffer(BaseModel):
    """Alternative offer (Plan Pausa, Annual, etc)."""
    type: str  # "plan_pausa", "annual_discount", "onboarding_support"
    name: str
    description: str
    price: float
    duration_days: int
    features: list[str]
    benefit_message: str


class CancellationInitiateResponse(BaseModel):
    """Response when starting cancellation flow."""
    status: str = "cancellation_initiated"
    impact_data: ImpactDataResponse
    churn_reason: str
    alternative_offers: list[DownsellOffer]
    billing_cycle_end: str


class PlanPausaRequest(BaseModel):
    """Request to activate Plan Pausa."""
    duration_days: int = Field(default=90, ge=30, le=365)


class PlanPausaResponse(BaseModel):
    """Response for Plan Pausa activation."""
    status: str
    message: str
    plan: str
    price: float
    duration_days: int
    resume_date: str
    google_api_permissions: str
    access_level: str


class CancellationConfirmRequest(BaseModel):
    """Request to confirm cancellation."""
    churn_reason: str
    churn_detail: Optional[str] = Field(None, max_length=500)


class CancellationConfirmResponse(BaseModel):
    """Response for confirmed cancellation."""
    status: str
    message: str
    user_id: str
    cancellation_date: str
    last_charge_date: str
    google_api_permissions_active_until: str
    access_level_after_cancellation: str
    cutoff_date: str
    metrics_pdf_url: str
    goodbye_email_sent: bool
    alerts_triggered: int


class CancellationLogoutResponse(BaseModel):
    """Frontend handoff response after cancellation flow is completed."""
    status: str
    redirect_url: str
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/impact-data",
    response_model=ImpactDataResponse,
    summary="Get cancellation impact data",
    description="Retrieves hours saved and impact stats for the cancellation modal.",
)
async def get_impact_data(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get impact data for cancellation confirmation modal.
    
    Shows:
    - Hours saved this month
    - Total reviews processed
    - AI response approval rate
    - Days subscribed
    - High-value customer indicator
    """
    try:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        data = CancellationService.get_impact_data_for_user(db, user.id)
        return ImpactDataResponse(**data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/initiate",
    response_model=CancellationInitiateResponse,
    summary="Initiate cancellation flow",
    description="Start the cancellation process and get alternative offers (Plan Pausa, annual, support).",
)
async def initiate_cancellation(
    churn_reason: str,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Initiate subscription cancellation with retention offers.
    
        Query param:
        - **churn_reason**: One of:
            - price_too_high (A. Es muy caro para mi volumen actual)
            - ease_of_use_difficulty (B. No entiendo cómo usar algunas funciones)
            - business_temporarily_closed (C. Mi negocio cerró temporalmente)
            - switched_competitor (D. Voy a probar otra herramienta)
    
    Returns:
    - Impact data (hours saved, stats)
    - Personalized alternative offers
    - Billing cycle end date
    
    Note: This is NOT final cancellation, just initiation with offer.
    """
    valid_reasons = [
        "price_too_high",
        "ease_of_use_difficulty",
        "business_temporarily_closed",
        "switched_competitor",
    ]
    
    if churn_reason not in valid_reasons:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid churn reason. Must be one of: {', '.join(valid_reasons)}",
        )
    
    try:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        result = CancellationService.start_cancellation_process(
            db=db,
            user_id=user.id,
            churn_reason=churn_reason,
        )
        return CancellationInitiateResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/plan-pausa",
    response_model=PlanPausaResponse,
    summary="Downgrade to Plan Pausa ($5/month read-only)",
    description="Instead of canceling, pause subscription for $5/month with read-only access.",
)
async def activate_plan_pausa(
    request: PlanPausaRequest,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Downgrade to Plan Pausa (retention via lower-tier offer).
    
    Benefits:
    - Only $5/month instead of $29
    - Pause for 30-365 days
    - Maintain read-only access to data
    - Google API permissions stay active
    - Can upgrade back anytime
    
    This is a downselling strategy to prevent churn.
    """
    try:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        result = CancellationService.activate_plan_pausa(
            db=db,
            user_id=user.id,
            duration_days=request.duration_days,
        )
        return PlanPausaResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/confirm",
    response_model=CancellationConfirmResponse,
    summary="Confirm final subscription cancellation",
    description="Complete the cancellation process and record churn survey data.",
)
async def confirm_cancellation(
    request: CancellationConfirmRequest,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Confirm and finalize subscription cancellation.
    
    Actions performed:
    1. ✅ Save churn survey (reason, feedback)
    2. ✅ Capture telemetry snapshot (hours, approval rate, active days)
    3. ✅ Ensure Google API permissions active until cycle end
    4. ✅ Record churn lifecycle event
    5. ✅ Run all churn alert checks (ease-of-use spike, rate spike, etc)
    
    Returns:
    - Cancellation confirmation
    - Google API permissions active until: [date]
    - Access level: read-only until cycle end
    - High/Critical alerts triggered count
    
    **Important:** Google API permissions REMAIN ACTIVE until the end of the current billing cycle.
    This ensures continuity of service during the transition period.
    """
    try:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        result = await CancellationService.confirm_cancellation(
            db=db,
            user_id=user.id,
            churn_reason=request.churn_reason,
            churn_detail=request.churn_detail,
        )
        return CancellationConfirmResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming cancellation: {str(e)}",
        )


@router.get(
    "/export-reviews.csv",
    summary="Export full review history as CSV",
    description="Download all user review history before account closure.",
)
async def export_review_history_csv(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """Export user review history in CSV format for off-platform retention."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    reviews = db.scalars(
        select(Review)
        .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
        .where(GoogleConnection.user_id == user_id)
        .order_by(Review.create_time.desc().nullslast(), Review.created_at.desc())
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "review_id",
            "location_id",
            "rating",
            "author",
            "comment",
            "create_time",
            "reply_action",
            "reply_public_text",
            "reply_sent_at",
        ]
    )

    for row in reviews:
        writer.writerow(
            [
                row.review_id,
                row.location_id,
                row.rating,
                row.author_display_name or "",
                (row.comment or "").replace("\r", " ").replace("\n", " "),
                row.create_time.isoformat() if row.create_time else "",
                row.reply_action or "",
                row.reply_public_text or "",
                row.reply_sent_at.isoformat() if row.reply_sent_at else "",
            ]
        )

    output.seek(0)
    stamp = datetime.utcnow().strftime("%Y%m%d")
    filename = f"lokigi_reviews_{user_id}_{stamp}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)


@router.post(
    "/logout",
    response_model=CancellationLogoutResponse,
    summary="Finalize cancellation flow and close session",
    description="Client handoff endpoint for redirecting user to public landing after cancellation.",
)
async def cancellation_logout() -> CancellationLogoutResponse:
    """Stateless logout handoff for UI flow completion."""
    return CancellationLogoutResponse(
        status="logged_out",
        redirect_url="/",
        message="Sesion finalizada. Gracias por usar Lokigi.",
    )
