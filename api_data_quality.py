"""
API de Evaluación de Calidad de Datos (Data Quality & NAP Consistency)
Endpoints para evaluar integridad de datos NAP y generar reportes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import Lead, DataQualityEvaluation
from schemas import (
    DataQualityEvaluationRequest,
    DataQualityEvaluationResponse,
    DataQualityReportSummary,
    DimensionScore,
    DataQualityAlert
)
from data_quality_service import NAPEvaluator
from auth import get_current_user

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])


@router.post("/evaluate", response_model=DataQualityEvaluationResponse)
async def evaluate_data_quality(
    request: DataQualityEvaluationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Evalúa la calidad de datos NAP de un lead
    Genera score de integridad y recomendaciones
    
    **Requiere autenticación: SUPERUSER**
    """
    # Verificar que el lead existe
    lead = db.query(Lead).filter(Lead.id == request.lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {request.lead_id} no encontrado"
        )
    
    # Preparar datos para el evaluador
    google_maps_data = {
        "name": request.google_maps_data.name,
        "phone": request.google_maps_data.phone,
        "address": request.google_maps_data.address,
        **(request.google_maps_extras or {})
    }
    
    facebook_data = None
    if request.facebook_data:
        facebook_data = {
            "name": request.facebook_data.name,
            "phone": request.facebook_data.phone,
            "address": request.facebook_data.address
        }
    
    instagram_data = None
    if request.instagram_data:
        instagram_data = {
            "name": request.instagram_data.name,
            "phone": request.instagram_data.phone,
            "address": request.instagram_data.address
        }
    
    website_data = None
    if request.website_data:
        website_data = {
            "name": request.website_data.name,
            "phone": request.website_data.phone,
            "address": request.website_data.address
        }
    
    # Convertir coordenadas a tuplas
    pin_coords = tuple(request.google_maps_coordinates) if request.google_maps_coordinates else None
    addr_coords = tuple(request.address_coordinates) if request.address_coordinates else None
    
    # Ejecutar evaluación
    evaluator = NAPEvaluator()
    results = evaluator.evaluate_full_quality(
        google_maps_data=google_maps_data,
        facebook_data=facebook_data,
        instagram_data=instagram_data,
        website_data=website_data,
        coordinates=pin_coords,
        address_coordinates=addr_coords
    )
    
    # Determinar plataformas evaluadas
    platforms_evaluated = ["google_maps"]
    if facebook_data:
        platforms_evaluated.append("facebook")
    if instagram_data:
        platforms_evaluated.append("instagram")
    if website_data:
        platforms_evaluated.append("website")
    
    # Guardar o actualizar evaluación en la base de datos
    existing_evaluation = db.query(DataQualityEvaluation).filter(
        DataQualityEvaluation.lead_id == request.lead_id
    ).first()
    
    if existing_evaluation:
        # Actualizar evaluación existente
        existing_evaluation.overall_score = results["overall_score"]
        existing_evaluation.name_consistency_score = results["dimensions"]["name_consistency"]["score"]
        existing_evaluation.phone_consistency_score = results["dimensions"]["phone_consistency"]["score"]
        existing_evaluation.address_consistency_score = results["dimensions"]["address_consistency"]["score"]
        existing_evaluation.location_accuracy_score = results["dimensions"]["location_accuracy"]["score"]
        existing_evaluation.completeness_score = results["dimensions"]["completeness"]["score"]
        existing_evaluation.evaluation_data = results
        existing_evaluation.alerts = results["alerts"]
        existing_evaluation.recommendations = results["recommendations"]
        existing_evaluation.requires_cleanup_service = results["requires_cleanup_service"]
        existing_evaluation.platforms_evaluated = platforms_evaluated
        existing_evaluation.updated_at = datetime.utcnow()
        
        db_evaluation = existing_evaluation
    else:
        # Crear nueva evaluación
        db_evaluation = DataQualityEvaluation(
            lead_id=request.lead_id,
            overall_score=results["overall_score"],
            name_consistency_score=results["dimensions"]["name_consistency"]["score"],
            phone_consistency_score=results["dimensions"]["phone_consistency"]["score"],
            address_consistency_score=results["dimensions"]["address_consistency"]["score"],
            location_accuracy_score=results["dimensions"]["location_accuracy"]["score"],
            completeness_score=results["dimensions"]["completeness"]["score"],
            evaluation_data=results,
            alerts=results["alerts"],
            recommendations=results["recommendations"],
            requires_cleanup_service=results["requires_cleanup_service"],
            platforms_evaluated=platforms_evaluated,
            status="completed"
        )
        db.add(db_evaluation)
    
    db.commit()
    db.refresh(db_evaluation)
    
    # Construir respuesta
    response = DataQualityEvaluationResponse(
        lead_id=request.lead_id,
        overall_score=results["overall_score"],
        name_consistency=DimensionScore(
            score=results["dimensions"]["name_consistency"]["score"],
            status=results["dimensions"]["name_consistency"]["status"],
            details=results["dimensions"]["name_consistency"]
        ),
        phone_consistency=DimensionScore(
            score=results["dimensions"]["phone_consistency"]["score"],
            status=results["dimensions"]["phone_consistency"]["status"],
            details=results["dimensions"]["phone_consistency"]
        ),
        address_consistency=DimensionScore(
            score=results["dimensions"]["address_consistency"]["score"],
            status=results["dimensions"]["address_consistency"]["status"],
            details=results["dimensions"]["address_consistency"]
        ),
        location_accuracy=DimensionScore(
            score=results["dimensions"]["location_accuracy"]["score"],
            status=results["dimensions"]["location_accuracy"]["status"],
            details=results["dimensions"]["location_accuracy"]
        ),
        completeness=DimensionScore(
            score=results["dimensions"]["completeness"]["score"],
            status=results["dimensions"]["completeness"]["status"],
            details=results["dimensions"]["completeness"]
        ),
        alerts=[DataQualityAlert(**alert) for alert in results["alerts"]],
        recommendations=results["recommendations"],
        requires_cleanup_service=results["requires_cleanup_service"],
        platforms_evaluated=platforms_evaluated,
        evaluated_at=db_evaluation.created_at
    )
    
    return response


@router.get("/report/{lead_id}", response_model=DataQualityEvaluationResponse)
async def get_data_quality_report(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene el reporte de calidad de datos de un lead
    
    **Requiere autenticación: SUPERUSER o WORKER**
    """
    # Verificar que el lead existe
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} no encontrado"
        )
    
    # Buscar evaluación
    evaluation = db.query(DataQualityEvaluation).filter(
        DataQualityEvaluation.lead_id == lead_id
    ).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe evaluación de calidad para el lead {lead_id}. Ejecute /evaluate primero."
        )
    
    # Reconstruir respuesta desde evaluation_data
    results = evaluation.evaluation_data
    
    response = DataQualityEvaluationResponse(
        lead_id=lead_id,
        overall_score=evaluation.overall_score,
        name_consistency=DimensionScore(
            score=results["dimensions"]["name_consistency"]["score"],
            status=results["dimensions"]["name_consistency"]["status"],
            details=results["dimensions"]["name_consistency"]
        ),
        phone_consistency=DimensionScore(
            score=results["dimensions"]["phone_consistency"]["score"],
            status=results["dimensions"]["phone_consistency"]["status"],
            details=results["dimensions"]["phone_consistency"]
        ),
        address_consistency=DimensionScore(
            score=results["dimensions"]["address_consistency"]["score"],
            status=results["dimensions"]["address_consistency"]["status"],
            details=results["dimensions"]["address_consistency"]
        ),
        location_accuracy=DimensionScore(
            score=results["dimensions"]["location_accuracy"]["score"],
            status=results["dimensions"]["location_accuracy"]["status"],
            details=results["dimensions"]["location_accuracy"]
        ),
        completeness=DimensionScore(
            score=results["dimensions"]["completeness"]["score"],
            status=results["dimensions"]["completeness"]["status"],
            details=results["dimensions"]["completeness"]
        ),
        alerts=[DataQualityAlert(**alert) for alert in evaluation.alerts],
        recommendations=evaluation.recommendations,
        requires_cleanup_service=evaluation.requires_cleanup_service,
        platforms_evaluated=evaluation.platforms_evaluated,
        evaluated_at=evaluation.created_at
    )
    
    return response


@router.get("/summary", response_model=List[DataQualityReportSummary])
async def get_all_evaluations_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene resumen de todas las evaluaciones de calidad de datos
    Útil para dashboard de administración
    
    **Requiere autenticación: SUPERUSER**
    """
    evaluations = db.query(DataQualityEvaluation).order_by(
        DataQualityEvaluation.overall_score.asc()  # Peores primero
    ).all()
    
    summaries = []
    for evaluation in evaluations:
        lead = db.query(Lead).filter(Lead.id == evaluation.lead_id).first()
        
        # Contar alertas críticas
        critical_alerts = sum(
            1 for alert in evaluation.alerts
            if alert.get("type") == "critical"
        )
        
        summary = DataQualityReportSummary(
            lead_id=evaluation.lead_id,
            business_name=lead.nombre_negocio if lead else "Unknown",
            overall_score=evaluation.overall_score,
            requires_cleanup_service=evaluation.requires_cleanup_service,
            critical_alerts_count=critical_alerts,
            evaluated_at=evaluation.created_at
        )
        summaries.append(summary)
    
    return summaries


@router.get("/cleanup-candidates", response_model=List[DataQualityReportSummary])
async def get_cleanup_service_candidates(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene lista de leads que requieren servicio de limpieza de datos ($99)
    Score < 90%
    
    **Requiere autenticación: SUPERUSER**
    """
    evaluations = db.query(DataQualityEvaluation).filter(
        DataQualityEvaluation.requires_cleanup_service == True
    ).order_by(
        DataQualityEvaluation.overall_score.asc()  # Peores primero
    ).all()
    
    candidates = []
    for evaluation in evaluations:
        lead = db.query(Lead).filter(Lead.id == evaluation.lead_id).first()
        
        if not lead:
            continue
        
        # Contar alertas críticas
        critical_alerts = sum(
            1 for alert in evaluation.alerts
            if alert.get("type") == "critical"
        )
        
        candidate = DataQualityReportSummary(
            lead_id=evaluation.lead_id,
            business_name=lead.nombre_negocio,
            overall_score=evaluation.overall_score,
            requires_cleanup_service=True,
            critical_alerts_count=critical_alerts,
            evaluated_at=evaluation.created_at
        )
        candidates.append(candidate)
    
    return candidates


@router.delete("/{lead_id}")
async def delete_evaluation(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Elimina una evaluación de calidad de datos
    
    **Requiere autenticación: SUPERUSER**
    """
    evaluation = db.query(DataQualityEvaluation).filter(
        DataQualityEvaluation.lead_id == lead_id
    ).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe evaluación para el lead {lead_id}"
        )
    
    db.delete(evaluation)
    db.commit()
    
    return {"message": f"Evaluación del lead {lead_id} eliminada exitosamente"}
