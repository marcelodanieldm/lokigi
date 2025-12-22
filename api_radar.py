"""
API de Radar Lokigi - Monitoreo Pasivo de Competidores (Suscripción $29/mes)
Endpoints para competitor tracking, alertas, y heatmaps dinámicos
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models import Lead, CompetitorSnapshot, RadarAlert, VisibilityHeatmap
from schemas import (
    RadarScanRequest,
    RadarScanResponse,
    CompetitorSnapshotResponse,
    CompetitorHistoryResponse,
    RadarAlertResponse,
    VisibilityHeatmapResponse,
    CompetitorComparisonResponse,
    RadarStatusResponse
)
from radar_service import CompetitorTracker, AlertGenerator, HeatmapGenerator
from auth import get_current_user

router = APIRouter(prefix="/api/radar", tags=["radar-lokigi"])


def verify_premium_subscription(lead: Lead):
    """Verifica que el lead sea suscriptor premium activo"""
    if not lead.premium_subscriber:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Radar Lokigi requiere suscripción premium ($29/mes). "
                   "Actualiza tu plan para acceder al monitoreo de competidores."
        )
    
    # Verificar que la suscripción esté activa
    if lead.subscription_status not in ["active", "trialing"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tu suscripción está {lead.subscription_status}. "
                   "Reactiva tu suscripción para continuar usando Radar Lokigi."
        )


@router.post("/scan-competitors", response_model=RadarScanResponse)
async def scan_competitors(
    request: RadarScanRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Escanea competidores y genera snapshots + alertas
    
    **Requiere:** Suscripción Premium ($29/mes)
    **Frecuencia recomendada:** 1 vez al mes (automático con cron)
    """
    # Verificar que el lead existe
    lead = db.query(Lead).filter(Lead.id == request.lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {request.lead_id} no encontrado"
        )
    
    # Verificar suscripción premium
    verify_premium_subscription(lead)
    
    # 1. Escanear competidores
    tracker = CompetitorTracker(db)
    scan_results = tracker.scan_all_competitors(
        lead_id=request.lead_id,
        competitors_data=request.competitors_data
    )
    
    # 2. Generar alertas basadas en movimientos detectados
    alert_gen = AlertGenerator(db)
    alerts_created = alert_gen.generate_alerts_from_scan(
        lead_id=request.lead_id,
        scan_results=scan_results
    )
    
    # 3. Actualizar heatmap si se proporcionaron coordenadas
    if request.business_coordinates and request.business_score is not None:
        heatmap_gen = HeatmapGenerator(db)
        heatmap_gen.generate_heatmap(
            lead_id=request.lead_id,
            business_coordinates=tuple(request.business_coordinates),
            business_score=request.business_score,
            competitors_data=request.competitors_data
        )
    
    # Contar movimientos detectados
    movements = sum(1 for r in scan_results if r.get("movement_detected"))
    
    return RadarScanResponse(
        lead_id=request.lead_id,
        scan_timestamp=datetime.utcnow(),
        competitors_scanned=len(scan_results),
        movements_detected=movements,
        alerts_generated=len(alerts_created),
        scan_results=scan_results
    )


@router.get("/alerts/{lead_id}", response_model=List[RadarAlertResponse])
async def get_radar_alerts(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    limit: int = 20
):
    """
    Obtiene alertas de Radar Lokigi de un lead
    
    **Requiere:** Suscripción Premium
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} no encontrado"
        )
    
    verify_premium_subscription(lead)
    
    alerts = db.query(RadarAlert).filter(
        RadarAlert.lead_id == lead_id
    ).order_by(RadarAlert.created_at.desc()).limit(limit).all()
    
    return alerts


@router.get("/competitor-history/{lead_id}/{competitor_name}", response_model=CompetitorHistoryResponse)
async def get_competitor_history(
    lead_id: int,
    competitor_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    limit: int = 12
):
    """
    Obtiene histórico de snapshots de un competidor (últimos 12 meses)
    
    **Requiere:** Suscripción Premium
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} no encontrado"
        )
    
    verify_premium_subscription(lead)
    
    tracker = CompetitorTracker(db)
    history = tracker.get_competitor_history(lead_id, competitor_name, limit)
    
    return CompetitorHistoryResponse(
        competitor_name=competitor_name,
        snapshots=history,
        total_snapshots=len(history)
    )


@router.get("/heatmap/{lead_id}", response_model=VisibilityHeatmapResponse)
async def get_visibility_heatmap(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene el mapa de calor de visibilidad más reciente
    
    **Requiere:** Suscripción Premium
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} no encontrado"
        )
    
    verify_premium_subscription(lead)
    
    heatmap_gen = HeatmapGenerator(db)
    heatmap_data = heatmap_gen.get_latest_heatmap(lead_id)
    
    if not heatmap_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay heatmap disponible. Ejecuta un scan de competidores primero."
        )
    
    # Buscar el objeto completo en BD
    heatmap = db.query(VisibilityHeatmap).filter(
        VisibilityHeatmap.id == heatmap_data["id"]
    ).first()
    
    return heatmap


@router.get("/comparison/{lead_id}", response_model=CompetitorComparisonResponse)
async def get_competitor_comparison(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Compara el score del negocio vs competidores
    Muestra ranking y posición competitiva
    
    **Requiere:** Suscripción Premium
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} no encontrado"
        )
    
    verify_premium_subscription(lead)
    
    # Obtener score del negocio
    business_score = lead.score_visibilidad or 0
    
    # Obtener últimos snapshots de cada competidor
    tracker = CompetitorTracker(db)
    competitors_summary = tracker.get_all_competitors_summary(lead_id)
    
    # Crear ranking (negocio + competidores)
    all_entities = [
        {"name": lead.nombre_negocio, "score": business_score, "is_business": True}
    ]
    
    for comp in competitors_summary["competitors"]:
        all_entities.append({
            "name": comp["name"],
            "score": comp["current_score"],
            "rating": comp.get("rating"),
            "review_count": comp.get("review_count"),
            "is_business": False
        })
    
    # Ordenar por score descendente
    all_entities.sort(key=lambda x: x["score"], reverse=True)
    
    # Encontrar posición del negocio
    business_rank = next(
        (i + 1 for i, e in enumerate(all_entities) if e.get("is_business")),
        len(all_entities)
    )
    
    return CompetitorComparisonResponse(
        business_score=business_score,
        business_rank=business_rank,
        total_competitors=len(all_entities) - 1,  # Excluir el negocio
        competitors=all_entities
    )


@router.get("/status/{lead_id}", response_model=RadarStatusResponse)
async def get_radar_status(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene el estado general del monitoreo de Radar Lokigi
    
    **Público** (no requiere premium, pero muestra status)
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} no encontrado"
        )
    
    # Obtener última fecha de scan
    last_snapshot = db.query(CompetitorSnapshot).filter(
        CompetitorSnapshot.lead_id == lead_id
    ).order_by(CompetitorSnapshot.created_at.desc()).first()
    
    last_scan_date = last_snapshot.created_at if last_snapshot else None
    next_scan_date = last_scan_date + timedelta(days=30) if last_scan_date else None
    
    # Contar competidores únicos
    unique_competitors = db.query(CompetitorSnapshot.competitor_name).filter(
        CompetitorSnapshot.lead_id == lead_id
    ).distinct().count()
    
    # Contar alertas pendientes
    pending_alerts = db.query(RadarAlert).filter(
        RadarAlert.lead_id == lead_id,
        RadarAlert.status == "pending"
    ).count()
    
    # Última fecha de heatmap
    last_heatmap = db.query(VisibilityHeatmap).filter(
        VisibilityHeatmap.lead_id == lead_id
    ).order_by(VisibilityHeatmap.created_at.desc()).first()
    
    latest_heatmap_date = last_heatmap.created_at if last_heatmap else None
    
    return RadarStatusResponse(
        lead_id=lead_id,
        is_premium_subscriber=lead.premium_subscriber,
        last_scan_date=last_scan_date,
        next_scan_date=next_scan_date,
        total_competitors_tracked=unique_competitors,
        pending_alerts=pending_alerts,
        latest_heatmap_date=latest_heatmap_date
    )


@router.post("/mark-alert-read/{alert_id}")
async def mark_alert_as_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Marca una alerta como leída
    
    **Requiere:** Autenticación
    """
    alert = db.query(RadarAlert).filter(RadarAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alerta {alert_id} no encontrada"
        )
    
    alert.status = "read"
    alert.read_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"Alerta {alert_id} marcada como leída"}


@router.delete("/alert/{alert_id}")
async def dismiss_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Descarta/elimina una alerta
    
    **Requiere:** Autenticación
    """
    alert = db.query(RadarAlert).filter(RadarAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alerta {alert_id} no encontrada"
        )
    
    alert.status = "dismissed"
    db.commit()
    
    return {"message": f"Alerta {alert_id} descartada"}
