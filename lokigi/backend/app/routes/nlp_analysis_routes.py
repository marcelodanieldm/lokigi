"""
API Endpoints for NLP Model Analysis
====================================

Exposes analysis of edited responses to identify model improvement opportunities.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models import User, Review, GoogleConnection
from app.nlp_edit_analysis import (
    analyze_user_edits,
    analyze_all_users_edits,
)
from app.starter_tip_service import generate_starter_tip


router = APIRouter(prefix="/api/nlp", tags=["nlp-analysis"])


def _require_user_by_header(db: Session, x_user_id: str) -> User:
    try:
        user_id = UUID(str(x_user_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header") from exc

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────────────────────────────────────


class ErrorPatternResponse(BaseModel):
    """Error pattern found in edits."""
    error_type: str
    frequency: int
    languages: list[str]
    ratings: list[int]
    sample_edits: list[dict]


class UserEditAnalysisResponse(BaseModel):
    """Response from user edit analysis endpoint."""
    user_id: str
    period_days: int
    total_reviews: int
    edited_reviews: int
    edit_rate_pct: float
    average_similarity_score: Optional[float] = None
    error_patterns: list[ErrorPatternResponse]
    system_prompt_suggestions: list[str]
    sample_edits: list[dict] = Field(default_factory=list)


class SystemicAnalysisResponse(BaseModel):
    """Response from systemic analysis endpoint."""
    total_edits_analyzed: int
    average_similarity_score: float
    most_common_errors: dict
    most_common_biases: dict
    recommended_prompt_overhaul: str


class StarterTipResponse(BaseModel):
    tip_del_dia: str
    focus: str
    confidence: float
    evidence_count: int
    supporting_signals: list[str] = Field(default_factory=list)
    tone: str
    is_fallback: bool
    fallback_reason: Optional[str] = None
    source: str
    reviews_analyzed: int
    generated_at: str
    model_provider: Optional[str] = None
    model_name: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/user-edit-analysis",
    response_model=UserEditAnalysisResponse,
    summary="Analyze edited responses for current user",
    description="Analyzes replies edited by the user to identify model improvement opportunities.",
)
async def get_user_edit_analysis(
    days: int = Query(90, ge=1, le=365),
    x_user_id: str = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """
    Analyze edits made by the current user.
    
    Query parameters:
    - **days**: Number of days to analyze (default: 90, max: 365)
    
    Returns:
    - edit_rate_pct: Percentage of AI responses that were edited
    - error_patterns: Top 10 error types found
    - system_prompt_suggestions: Actionable recommendations
    - sample_edits: Examples of edits made
    
    Example:
    ```
    GET /api/nlp/user-edit-analysis?days=30
    ```
    
    Response includes:
    - "more_formal": User had to make responses less formal
    - "missing_author_name": Model forgot to use reviewer name
    - "missing_business_name": Model didn't reference business name
    """
    try:
        user = _require_user_by_header(db, x_user_id)
        result = analyze_user_edits(db, str(user.id), days=days)
        
        return UserEditAnalysisResponse(
            user_id=result['user_id'],
            period_days=result['period_days'],
            total_reviews=result['total_reviews'],
            edited_reviews=result['edited_reviews'],
            edit_rate_pct=result['edit_rate_pct'],
            average_similarity_score=result.get('average_similarity_score'),
            error_patterns=[
                ErrorPatternResponse(**ep) for ep in result['error_patterns']
            ],
            system_prompt_suggestions=result['system_prompt_suggestions'],
            sample_edits=result.get('sample_edits', []),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing edits: {str(e)}",
        )


@router.get(
    "/systemic-analysis",
    response_model=SystemicAnalysisResponse,
    summary="Analyze all users' edits (admin only)",
    description="Analyzes all users' edited responses to identify systemic model issues.",
)
async def get_systemic_analysis(
    days: int = Query(30, ge=1, le=365),
    x_user_id: str = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """
    Analyze edits ACROSS ALL USERS to find systemic patterns.
    
    ⚠️ Admin only - requires elevated permissions
    
    Query parameters:
    - **days**: Number of days to analyze (default: 30)
    
    Returns:
    - total_edits_analyzed: How many edited responses were found
    - average_similarity_score: How different original vs edited (0-1)
    - most_common_errors: Error types sorted by frequency
    - most_common_biases: Bias types detected
    - recommended_prompt_overhaul: Specific prompt changes
    
    Example response:
    ```json
    {
      "total_edits_analyzed": 542,
      "average_similarity_score": 0.82,
      "most_common_errors": {
        "more_formal": 156,
        "missing_author_name": 98,
        "missing_business_name": 67
      },
      "most_common_biases": {
        "gender_bias": 12,
        "inappropriate_assumption": 8
      },
      "recommended_prompt_overhaul": "## Changes needed..."
    }
    ```
    """
    # TODO: Add admin check
    # if not user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        _ = _require_user_by_header(db, x_user_id)
        result = analyze_all_users_edits(db, days=days)
        
        return SystemicAnalysisResponse(
            total_edits_analyzed=result['total_edits_analyzed'],
            average_similarity_score=result['average_similarity_score'],
            most_common_errors=result['most_common_errors'],
            most_common_biases=result['most_common_biases'],
            recommended_prompt_overhaul=result['recommended_prompt_overhaul'],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing systemic patterns: {str(e)}",
        )


@router.post(
    "/export-training-dataset",
    summary="Export edits as training data",
    description="Export all edited responses for model retraining.",
)
async def export_training_dataset(
    days: int = Query(90, ge=1, le=365),
    x_user_id: str = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    """
    Export dataset of edited responses for model retraining.
    
    Returns JSONL format suitable for:
    - OpenAI fine-tuning
    - Anthropic prompt engineering
    - Local LLM retraining
    
    Example:
    ```
    POST /api/nlp/export-training-dataset?days=90
    
    Response:
    {
      "file_path": "training_data_2026_04_18.jsonl",
      "total_pairs": 542,
      "download_url": "https://...",
      "next_steps": "Use with your fine-tuning pipeline"
    }
    ```
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    from app.models import Review
    from app.nlp_edit_analysis import analyze_single_edit
    import json
    from pathlib import Path
    
    try:
        _ = _require_user_by_header(db, x_user_id)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all edits
        reviews = db.execute(
            select(Review)
            .where(
                and_(
                    Review.reply_public_text.isnot(None),
                    Review.reply_approved_text.isnot(None),
                    Review.reply_approved_text != Review.reply_public_text,
                    Review.reply_sent_at >= cutoff_date,
                )
            )
        ).scalars().all()
        
        # Convert to training format
        training_pairs = []
        for review in reviews:
            analysis = analyze_single_edit(review)
            if analysis:
                pair = {
                    'original_response': analysis.original_reply,
                    'edited_response': analysis.edited_reply,
                    'rating': analysis.rating,
                    'language': analysis.language,
                    'error_types': analysis.error_categories,
                    'bias_flags': analysis.bias_flags,
                    'similarity_score': round(analysis.similarity_score, 3),
                }
                training_pairs.append(pair)
        
        # Create file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = Path(f"exports/training_data_{timestamp}.jsonl")
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for pair in training_pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + '\n')
        
        return {
            "status": "success",
            "file_path": str(file_path),
            "total_pairs": len(training_pairs),
            "timestamp": timestamp,
            "period_days": days,
            "format": "JSONL",
            "next_steps": [
                "1. Download the dataset",
                "2. Review for patterns",
                "3. Use for fine-tuning (OpenAI, Anthropic, or local LLM)",
                "4. A/B test improved model against baseline",
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting dataset: {str(e)}",
        )


@router.get(
    "/starter-tip-of-day",
    response_model=StarterTipResponse,
    summary="Generate Starter dashboard Tip of the Day",
    description="Builds a context-aware tip from the latest 10 reviews with automatic fallback when signal is weak.",
)
async def get_starter_tip_of_day(
    business_type: str = Query("negocio local", min_length=2, max_length=80),
    location: str = Query("tu zona", min_length=2, max_length=80),
    x_user_id: str = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    try:
        user = _require_user_by_header(db, x_user_id)
        rows = db.execute(
            select(Review.comment, GoogleConnection.business_name)
            .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
            .where(GoogleConnection.user_id == user.id)
            .order_by(Review.create_time.desc().nullslast(), Review.created_at.desc())
            .limit(10)
        ).all()

        latest_reviews = [str(comment or "").strip() for comment, _ in rows if str(comment or "").strip()]
        business_name = next((name for _, name in rows if name), None) or "tu negocio"

        tip = generate_starter_tip(
            business_name=business_name,
            business_type=business_type,
            location=location,
            reviews=latest_reviews,
        )
        return StarterTipResponse(**tip)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Starter tip: {str(e)}",
        )
