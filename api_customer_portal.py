"""
API de Customer Portal - Acceso seguro para clientes
Solo pueden ver sus propios datos (reportes, pagos, Radar)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import User, Lead, Order, Task, RadarSubscription, RadarAlert, UserRole
from schemas import (
    LeadResponse, OrderResponse, TaskResponse,
    RadarSubscriptionResponse, RadarAlertResponse
)
from auth import get_current_user, require_customer
from security_policies import SecurityPolicy

router = APIRouter(prefix="/api/customer", tags=["customer-portal"])


@router.get("/me")
async def get_customer_profile(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Obtener perfil del cliente autenticado
    """
    if not current_user.customer_lead_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente sin negocio asociado"
        )
    
    # Obtener datos del lead/negocio
    lead = db.query(Lead).filter(Lead.id == current_user.customer_lead_id).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negocio no encontrado"
        )
    
    # Verificar si tiene suscripción Radar activa
    radar_sub = db.query(RadarSubscription)\
        .filter(RadarSubscription.lead_id == lead.id)\
        .first()
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.value,
            "created_at": current_user.created_at
        },
        "business": {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "address": lead.address,
            "score_visibilidad": lead.score_visibilidad
        },
        "radar_subscription": {
            "active": radar_sub is not None and radar_sub.status in ["active", "trial"],
            "status": radar_sub.status if radar_sub else None,
            "trial_end": radar_sub.trial_end if radar_sub else None
        }
    }


@router.get("/reports")
async def get_my_reports(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Ver reportes de auditoría del negocio del cliente
    Solo puede ver sus propios reportes
    """
    SecurityPolicy.validate_access_to_lead(
        current_user,
        current_user.customer_lead_id,
        db
    )
    
    lead = db.query(Lead).filter(Lead.id == current_user.customer_lead_id).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negocio no encontrado"
        )
    
    return {
        "lead_id": lead.id,
        "business_name": lead.name,
        "visibility_score": lead.score_visibilidad,
        "audit_report": lead.audit_report,
        "generated_at": lead.created_at,
        "last_updated": lead.updated_at
    }


@router.get("/orders", response_model=List[dict])
async def get_my_orders(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Ver historial de pagos/órdenes del cliente
    Solo puede ver sus propias órdenes
    """
    query = db.query(Order)
    
    # Aplicar política de seguridad
    query = SecurityPolicy.filter_orders_by_user(query, current_user)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return [
        {
            "id": order.id,
            "product": order.product_type,
            "status": order.status,
            "amount": order.amount,
            "created_at": order.created_at,
            "completed_at": order.completed_at
        }
        for order in orders
    ]


@router.get("/tasks", response_model=List[dict])
async def get_my_tasks(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Ver tareas/servicios relacionados con las órdenes del cliente
    Solo puede ver tareas de sus propias órdenes
    """
    query = db.query(Task)
    
    # Aplicar política de seguridad
    query = SecurityPolicy.filter_tasks_by_user(query, current_user)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    return [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "status": task.status,
            "priority": task.priority,
            "created_at": task.created_at,
            "completed_at": task.completed_at
        }
        for task in tasks
    ]


@router.get("/radar/subscription")
async def get_my_radar_subscription(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Ver suscripción Radar del cliente (si existe)
    Solo puede ver su propia suscripción
    """
    SecurityPolicy.validate_access_to_lead(
        current_user,
        current_user.customer_lead_id,
        db
    )
    
    subscription = db.query(RadarSubscription)\
        .filter(RadarSubscription.lead_id == current_user.customer_lead_id)\
        .first()
    
    if not subscription:
        return {
            "has_subscription": False,
            "message": "No tienes una suscripción Radar activa"
        }
    
    return {
        "has_subscription": True,
        "subscription": {
            "id": subscription.id,
            "status": subscription.status,
            "monthly_price": subscription.monthly_price,
            "trial_end": subscription.trial_end,
            "current_period_end": subscription.current_period_end,
            "competitors_tracked": len(subscription.competitors_to_track),
            "total_alerts_sent": subscription.total_alerts_sent,
            "last_monitoring_at": subscription.last_monitoring_at,
            "next_monitoring_at": subscription.next_monitoring_at
        }
    }


@router.get("/radar/alerts", response_model=List[dict])
async def get_my_radar_alerts(
    current_user: User = Depends(require_customer),
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Ver alertas Radar del cliente
    Solo puede ver sus propias alertas
    """
    query = db.query(RadarAlert)
    
    # Aplicar política de seguridad
    query = SecurityPolicy.filter_radar_alerts_by_user(query, current_user)
    
    if unread_only:
        query = query.filter(RadarAlert.read_at.is_(None))
    
    alerts = query.order_by(RadarAlert.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": alert.id,
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity,
            "alert_type": alert.alert_type,
            "is_read": alert.read_at is not None,
            "created_at": alert.created_at
        }
        for alert in alerts
    ]


@router.post("/radar/alerts/{alert_id}/read")
async def mark_my_alert_as_read(
    alert_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Marcar una alerta como leída
    Solo puede marcar sus propias alertas
    """
    alert = db.query(RadarAlert).filter(RadarAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    
    # Verificar que la alerta pertenece al cliente
    SecurityPolicy.validate_access_to_lead(
        current_user,
        alert.lead_id,
        db
    )
    
    if not alert.read_at:
        alert.read_at = datetime.utcnow()
        db.commit()
    
    return {"message": "Alerta marcada como leída"}


@router.get("/radar/heatmap/latest")
async def get_my_latest_heatmap(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Ver mapa de calor más reciente del cliente
    Solo puede ver su propio heatmap
    """
    from models import VisibilityHeatmap
    
    SecurityPolicy.validate_access_to_lead(
        current_user,
        current_user.customer_lead_id,
        db
    )
    
    heatmap = db.query(VisibilityHeatmap)\
        .filter(VisibilityHeatmap.lead_id == current_user.customer_lead_id)\
        .order_by(VisibilityHeatmap.created_at.desc())\
        .first()
    
    if not heatmap:
        return {
            "has_heatmap": False,
            "message": "No hay mapas de calor disponibles"
        }
    
    return {
        "has_heatmap": True,
        "heatmap": {
            "id": heatmap.id,
            "center_coordinates": heatmap.center_coordinates,
            "radius_meters": heatmap.radius_meters,
            "area_dominance_score": heatmap.area_dominance_score,
            "area_growth_percent": heatmap.area_growth_percent,
            "competitor_density": heatmap.competitor_density,
            "competitors_in_area": heatmap.competitors_in_area,
            "created_at": heatmap.created_at
        }
    }


@router.put("/profile")
async def update_my_profile(
    full_name: str = None,
    email: str = None,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Actualizar perfil del cliente
    Solo puede modificar su propio perfil
    """
    if full_name:
        current_user.full_name = full_name
    
    if email:
        # Verificar que el nuevo email no esté en uso
        existing = db.query(User)\
            .filter(User.email == email)\
            .filter(User.id != current_user.id)\
            .first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso"
            )
        
        current_user.email = email
    
    db.commit()
    
    return {
        "message": "Perfil actualizado exitosamente",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name
        }
    }


@router.get("/dashboard/summary")
async def get_customer_dashboard_summary(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Dashboard resumen para el cliente
    Vista consolidada de toda su información
    """
    SecurityPolicy.validate_access_to_lead(
        current_user,
        current_user.customer_lead_id,
        db
    )
    
    # Obtener datos básicos
    lead = db.query(Lead).filter(Lead.id == current_user.customer_lead_id).first()
    
    # Contar órdenes
    orders_count = db.query(Order)\
        .filter(Order.lead_id == current_user.customer_lead_id)\
        .count()
    
    # Contar tareas pendientes
    pending_tasks = db.query(Task)\
        .join(Order)\
        .filter(Order.lead_id == current_user.customer_lead_id)\
        .filter(Task.status.in_(["pending", "in_progress"]))\
        .count()
    
    # Verificar suscripción Radar
    radar_sub = db.query(RadarSubscription)\
        .filter(RadarSubscription.lead_id == current_user.customer_lead_id)\
        .first()
    
    # Alertas no leídas
    unread_alerts = 0
    if radar_sub:
        unread_alerts = db.query(RadarAlert)\
            .filter(RadarAlert.lead_id == current_user.customer_lead_id)\
            .filter(RadarAlert.read_at.is_(None))\
            .count()
    
    return {
        "business": {
            "name": lead.name,
            "visibility_score": lead.score_visibilidad,
            "rating": lead.rating,
            "reviews_count": lead.reviews_count
        },
        "orders": {
            "total": orders_count
        },
        "tasks": {
            "pending": pending_tasks
        },
        "radar": {
            "active": radar_sub is not None and radar_sub.status in ["active", "trial"],
            "unread_alerts": unread_alerts
        }
    }
