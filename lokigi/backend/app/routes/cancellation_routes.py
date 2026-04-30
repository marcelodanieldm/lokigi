"""Cancellation & retention API endpoints.

POST   /api/cancellation/impact-data      - Get impact data for modal
POST   /api/cancellation/initiate          - Start cancellation flow
POST   /api/cancellation/plan-pausa        - Downgrade to Plan Pausa
POST   /api/cancellation/confirm           - Confirm final cancellation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from uuid import UUID
from typing import Optional
from datetime import datetime

import pandas as pd

from app.database import get_db
from app.models import GoogleConnection, Review, User
from app.cancellation_service import CancellationService

router = APIRouter(prefix="/api/cancellation", tags=["cancellation"])


def build_reviews_export_response(db: Session, user_id: UUID) -> Response:
    """Build the CSV export used by both API and SSR cancellation flows."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    reviews = db.scalars(
        select(Review)
        .options(selectinload(Review.pending_response))
        .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
        .where(GoogleConnection.user_id == user_id)
        .order_by(Review.create_time.desc().nullslast(), Review.created_at.desc())
    ).all()

    rows: list[dict[str, str | int]] = []
    for review in reviews:
        pending_response = review.pending_response
        lokigi_reply = (
            review.reply_approved_text
            or (pending_response.approved_text if pending_response else None)
            or review.reply_public_text
            or (pending_response.draft_text if pending_response else None)
            or ""
        )
        review_date = review.create_time or review.created_at
        rows.append(
            {
                "Fecha": review_date.strftime("%Y-%m-%d %H:%M") if review_date else "",
                "Cliente": review.author_display_name or "Cliente anónimo",
                "Estrellas": review.rating or "",
                "Reseña Original": (review.comment or "").replace("\r", " ").replace("\n", " ").strip(),
                "Respuesta de Lokigi": str(lokigi_reply).replace("\r", " ").replace("\n", " ").strip(),
            }
        )

    dataframe = pd.DataFrame(
        rows,
        columns=["Fecha", "Cliente", "Estrellas", "Reseña Original", "Respuesta de Lokigi"],
    )
    csv_content = dataframe.to_csv(index=False).encode("utf-8-sig")
    headers = {"Content-Disposition": 'attachment; filename="mi_historial_lokigi.csv"'}
    return Response(content=csv_content, media_type="text/csv", headers=headers)


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


class FeedbackOption(BaseModel):
    """Single-click exit survey option."""
    key: str
    label: str
    description: str


class CancellationInitiateResponse(BaseModel):
    """Response when starting cancellation flow."""
    status: str = "cancellation_initiated"
    impact_data: ImpactDataResponse
    churn_reason: str
    feedback_options: list[FeedbackOption]
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
    reviews_csv_url: str
    logout_url: str
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
            - price (Precio)
            - difficulty (Dificultad)
            - business_closed (Cierre de negocio)
    
    Returns:
    - Impact data (hours saved, stats)
    - Personalized alternative offers
    - Billing cycle end date
    
    Note: This is NOT final cancellation, just initiation with offer.
    """
    valid_reasons = CancellationService.allowed_feedback_reasons()
    
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
    valid_reasons = CancellationService.allowed_feedback_reasons()
    if request.churn_reason not in valid_reasons:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid churn reason. Must be one of: {', '.join(valid_reasons)}",
        )

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
    return build_reviews_export_response(db, user_id)


@router.post(
    "/logout",
    summary="Finalize cancellation flow and close session",
    description="Delete cancellation/session cookies and redirect the user to the login screen.",
)
async def cancellation_logout() -> RedirectResponse:
    """Best-effort session cleanup followed by login redirect."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    for cookie_name in (
        "session_id",
        "session",
        "sessionid",
        "lokigi_session",
        "access_token",
        "refresh_token",
    ):
        response.delete_cookie(cookie_name, path="/")
    return response
