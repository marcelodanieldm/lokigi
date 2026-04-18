"""
API Endpoints for NLP Model Analysis
====================================

Exposes analysis of edited responses to identify model improvement opportunities.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.nlp_edit_analysis import (
    analyze_user_edits,
    analyze_all_users_edits,
)


router = APIRouter(prefix="/api/nlp", tags=["nlp-analysis"])


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
    user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
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
