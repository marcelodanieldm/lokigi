"""
API de Radar Lokigi - Sistema de Monitoreo de Competencia ($29/mes)
Endpoints para suscripción, monitoreo y alertas
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import (
    Lead, RadarSubscription, CompetitorSnapshot, RadarAlert,
    VisibilityHeatmap, SubscriptionStatus
)
from schemas import (
    RadarSubscriptionCreate, RadarSubscriptionResponse,
    CompetitorSnapshotResponse, RadarAlertResponse,
    VisibilityHeatmapResponse, MonitoringResultResponse
)
from competitor_monitoring_service import CompetitorMonitoringService
from radar_service import RadarService
from auth import get_current_user, require_superuser

router = APIRouter(prefix="/api/radar", tags=["radar-lokigi"])


@router.post("/subscribe", response_model=RadarSubscriptionResponse)
async def create_radar_subscription(
    lead_id: int,
    competitor_ids: List[int],
    alert_email: Optional[str] = None,
    alert_phone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Crear suscripción a Radar Lokigi para un lead
    
    - **lead_id**: ID del lead/cliente a monitorear
    - **competitor_ids**: Lista de IDs de competidores a rastrear (máx 5)
    - **alert_email**: Email para recibir alertas
    - **alert_phone**: Teléfono para WhatsApp alerts
    
    **Precio: $29/mes** (incluye 30 días de trial)
    """
    # Verificar que el lead existe
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead no encontrado"
        )
    
    # Verificar que no tenga ya una suscripción activa
    existing = db.query(RadarSubscription)\
        .filter(RadarSubscription.lead_id == lead_id)\
        .filter(RadarSubscription.status.in_([
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL
        ]))\
        .first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El lead ya tiene una suscripción activa"
        )
    
    # Validar competidores
    if not competitor_ids or len(competitor_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe especificar entre 1 y 5 competidores"
        )
    
    # Verificar que los competidores existen
    competitors = db.query(Lead).filter(Lead.id.in_(competitor_ids)).all()
    if len(competitors) != len(competitor_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o más competidores no fueron encontrados"
        )
    
    # Crear suscripción con trial de 30 días
    trial_start = datetime.utcnow()
    trial_end = trial_start + timedelta(days=30)
    
    subscription = RadarSubscription(
        lead_id=lead_id,
        status=SubscriptionStatus.TRIAL,
        monthly_price=29.0,
        currency="USD",
        trial_start=trial_start,
        trial_end=trial_end,
        current_period_start=trial_start,
        current_period_end=trial_end,
        competitors_to_track=competitor_ids,
        monitoring_frequency_days=30,
        next_monitoring_at=datetime.utcnow() + timedelta(days=1),  # Primer monitoreo mañana
        alerts_enabled=True,
        alert_email=alert_email or lead.email,
        alert_phone=alert_phone or lead.phone,
        created_at=datetime.utcnow()
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    return subscription


@router.get("/subscription/{lead_id}", response_model=RadarSubscriptionResponse)
async def get_radar_subscription(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener la suscripción Radar de un lead
    """
    subscription = db.query(RadarSubscription)\
        .filter(RadarSubscription.lead_id == lead_id)\
        .first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró suscripción Radar para este lead"
        )
    
    return subscription


@router.post("/subscription/{subscription_id}/cancel")
async def cancel_radar_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cancelar una suscripción Radar
    """
    subscription = db.query(RadarSubscription)\
        .filter(RadarSubscription.id == subscription_id)\
        .first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )
    
    if subscription.status == SubscriptionStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La suscripción ya está cancelada"
        )
    
    subscription.status = SubscriptionStatus.CANCELLED
    subscription.cancelled_at = datetime.utcnow()
    
    # TODO: Cancelar en Stripe si existe stripe_subscription_id
    
    db.commit()
    
    return {
        "message": "Suscripción cancelada exitosamente",
        "subscription_id": subscription_id,
        "cancelled_at": subscription.cancelled_at
    }


@router.post("/monitor/{subscription_id}", response_model=MonitoringResultResponse)
async def trigger_competitor_monitoring(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser())
):
    """
    Ejecutar monitoreo manual de competidores (solo superuser)
    
    En producción, esto se ejecuta automáticamente vía cron job
    """
    radar_service = RadarService()
    
    results = CompetitorMonitoringService.monitor_subscription_competitors(
        db=db,
        subscription_id=subscription_id,
        radar_service=radar_service
    )
    
    if "error" in results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=results["error"]
        )
    
    return results


@router.get("/alerts/{lead_id}", response_model=List[RadarAlertResponse])
async def get_lead_alerts(
    lead_id: int,
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Obtener alertas de un lead
    
    - **unread_only**: Solo alertas no leídas
    - **limit**: Número máximo de alertas a retornar
    """
    query = db.query(RadarAlert).filter(RadarAlert.lead_id == lead_id)
    
    if unread_only:
        query = query.filter(RadarAlert.read_at.is_(None))
    
    alerts = query.order_by(RadarAlert.created_at.desc()).limit(limit).all()
    
    return alerts


@router.post("/alerts/{alert_id}/read")
async def mark_alert_as_read(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Marcar una alerta como leída
    """
    alert = db.query(RadarAlert).filter(RadarAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    
    if not alert.read_at:
        alert.read_at = datetime.utcnow()
        db.commit()
    
    return {"message": "Alerta marcada como leída"}


@router.get("/snapshots/{subscription_id}", response_model=List[CompetitorSnapshotResponse])
async def get_competitor_snapshots(
    subscription_id: int,
    competitor_id: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Obtener snapshots de competidores de una suscripción
    
    - **competitor_id**: Filtrar por competidor específico (opcional)
    - **limit**: Número máximo de snapshots
    """
    query = db.query(CompetitorSnapshot)\
        .filter(CompetitorSnapshot.subscription_id == subscription_id)
    
    if competitor_id:
        query = query.filter(CompetitorSnapshot.competitor_id == competitor_id)
    
    snapshots = query.order_by(CompetitorSnapshot.captured_at.desc())\
        .limit(limit)\
        .all()
    
    return snapshots


@router.get("/heatmap/{lead_id}/latest", response_model=VisibilityHeatmapResponse)
async def get_latest_heatmap(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener el mapa de calor más reciente de un lead
    """
    heatmap = db.query(VisibilityHeatmap)\
        .filter(VisibilityHeatmap.lead_id == lead_id)\
        .order_by(VisibilityHeatmap.created_at.desc())\
        .first()
    
    if not heatmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay heatmap disponible para este lead"
        )
    
    return heatmap


@router.get("/heatmap/{lead_id}/history", response_model=List[VisibilityHeatmapResponse])
async def get_heatmap_history(
    lead_id: int,
    limit: int = 12,  # 1 año de historia mensual
    db: Session = Depends(get_db)
):
    """
    Obtener historial de mapas de calor de un lead
    """
    heatmaps = db.query(VisibilityHeatmap)\
        .filter(VisibilityHeatmap.lead_id == lead_id)\
        .order_by(VisibilityHeatmap.created_at.desc())\
        .limit(limit)\
        .all()
    
    return heatmaps


@router.post("/heatmap/{subscription_id}/generate", response_model=VisibilityHeatmapResponse)
async def generate_heatmap(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser())
):
    """
    Generar mapa de calor manualmente (solo superuser)
    """
    radar_service = RadarService()
    
    heatmap = CompetitorMonitoringService.update_visibility_heatmap(
        db=db,
        subscription_id=subscription_id,
        radar_service=radar_service
    )
    
    if not heatmap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo generar el heatmap"
        )
    
    return heatmap


@router.get("/dashboard/summary")
async def get_radar_dashboard_summary(
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser())
):
    """
    Dashboard resumen de todas las suscripciones Radar (solo superuser)
    """
    # Total de suscripciones por estado
    subscriptions = db.query(RadarSubscription).all()
    
    total = len(subscriptions)
    active = len([s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE])
    trial = len([s for s in subscriptions if s.status == SubscriptionStatus.TRIAL])
    cancelled = len([s for s in subscriptions if s.status == SubscriptionStatus.CANCELLED])
    
    # Revenue mensual recurrente (MRR)
    mrr = sum(s.monthly_price for s in subscriptions 
              if s.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
    
    # Total de alertas generadas
    total_alerts = sum(s.total_alerts_sent for s in subscriptions)
    
    # Alertas pendientes (no leídas)
    unread_alerts = db.query(RadarAlert)\
        .filter(RadarAlert.read_at.is_(None))\
        .count()
    
    return {
        "total_subscriptions": total,
        "active_subscriptions": active,
        "trial_subscriptions": trial,
        "cancelled_subscriptions": cancelled,
        "monthly_recurring_revenue": mrr,
        "total_alerts_sent": total_alerts,
        "unread_alerts": unread_alerts,
        "by_status": {
            "active": active,
            "trial": trial,
            "cancelled": cancelled,
            "expired": len([s for s in subscriptions if s.status == SubscriptionStatus.EXPIRED])
        }
    }


@router.post("/cron/monitor-all")
async def cron_monitor_all_subscriptions(
    db: Session = Depends(get_db),
    api_key: str = None  # TODO: Validar API key para cron job
):
    """
    Endpoint para cron job: Monitorear todas las suscripciones que lo necesitan
    
    Debe ser llamado por el cron job diariamente
    """
    # TODO: Validar API key
    
    radar_service = RadarService()
    subscriptions = CompetitorMonitoringService.get_subscriptions_to_monitor(db)
    
    results = {
        "executed_at": datetime.utcnow().isoformat(),
        "subscriptions_checked": len(subscriptions),
        "monitoring_results": []
    }
    
    for subscription in subscriptions:
        try:
            result = CompetitorMonitoringService.monitor_subscription_competitors(
                db=db,
                subscription_id=subscription.id,
                radar_service=radar_service
            )
            results["monitoring_results"].append(result)
            
            # Generar heatmap si es el día apropiado (cada 30 días)
            if subscription.last_monitoring_at:
                days_since_last = (datetime.utcnow() - subscription.last_monitoring_at).days
                if days_since_last >= 30:
                    CompetitorMonitoringService.update_visibility_heatmap(
                        db=db,
                        subscription_id=subscription.id,
                        radar_service=radar_service
                    )
        
        except Exception as e:
            results["monitoring_results"].append({
                "subscription_id": subscription.id,
                "error": str(e)
            })
    
    return results
