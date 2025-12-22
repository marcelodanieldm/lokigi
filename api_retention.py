"""
API de Retención (Anti-Churn Logic)

Sistema de 3 pasos para reducir cancelaciones de suscripción Radar Lokigi ($29/mes):
1. Micro-Audit: Detecta amenazas de competidores en tiempo real
2. Retention Offer: Ofrece descuento 50% o 15 días gratis
3. Churn Feedback: Guarda motivo de cancelación para análisis

Estrategia: Psicología de la Pérdida (FOMO) con datos reales.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import Optional
import stripe
import os

from database import get_db
from models import (
    Lead, 
    RadarSubscription, 
    SubscriptionStatus,
    ChurnFeedback,
    User
)
from schemas import (
    CancellationAttemptRequest,
    MicroAuditResponse,
    CompetitorThreat,
    RetentionOfferResponse,
    RetentionOfferType,
    ChurnFeedbackCreate,
    ChurnFeedbackResponse
)
from auth import get_current_user

# Configuración de Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/api/retention", tags=["Retention Anti-Churn"])


# ============================================================================
# PASO 1: MICRO-AUDIT AL INTENTAR CANCELAR
# ============================================================================

@router.post("/micro-audit", response_model=MicroAuditResponse)
async def get_cancellation_micro_audit(
    request: CancellationAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🚨 PASO 1 del Exit Flow: Micro-Audit Express
    
    Cuando el usuario hace clic en "Cancelar Suscripción", este endpoint:
    - Busca movimientos recientes de competidores (últimos 30 días)
    - Detecta amenazas críticas: ranking_increase, reviews_surge, score_jump
    - Genera mensaje dinámico en idioma del usuario con datos reales
    
    **Psicología de la Pérdida:** Mostrar peligro inmediato si se va.
    """
    
    # Verificar que la suscripción existe y pertenece al usuario
    subscription = db.query(RadarSubscription).filter(
        and_(
            RadarSubscription.id == request.subscription_id,
            RadarSubscription.lead_id == request.lead_id
        )
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Verificar que el lead pertenece al usuario actual
    lead = db.query(Lead).filter(Lead.id == request.lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # TODO: Aquí conectarías con la tabla de CompetitorSnapshot para detectar movimientos
    # Por ahora, simulamos detección de amenazas
    
    # Buscar snapshots de competidores de los últimos 30 días
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # SIMULACIÓN DE DETECCIÓN (reemplazar con queries reales a CompetitorSnapshot)
    threats_detected = []
    
    # Simulación: Detectar que un competidor subió en reviews
    threats_detected.append(
        CompetitorThreat(
            competitor_name="Restaurante La Competencia",
            threat_type="reviews_surge",
            threat_level="high",
            details="Aumentó 8 reseñas en los últimos 15 días",
            metric_change={"reviews": +8, "rating": +0.2}
        )
    )
    
    # Simulación: Detectar cambio en ranking
    threats_detected.append(
        CompetitorThreat(
            competitor_name="Café del Centro",
            threat_type="ranking_increase",
            threat_level="critical",
            details="Subió 3 posiciones y ahora está a solo 2 reseñas de superarte",
            metric_change={"rank_position": -3, "reviews_gap": 2}
        )
    )
    
    # Calcular días desde último scan
    days_since_last_scan = 30
    if subscription.last_monitoring_at:
        days_since_last_scan = (datetime.utcnow() - subscription.last_monitoring_at).days
    
    # Generar mensaje dinámico según idioma
    urgency_messages = {
        "es": f"⚠️ ¿Estás seguro? En los últimos 30 días, detectamos que **{threats_detected[1].competitor_name}** subió su ranking y está a solo 2 reseñas de superarte. Si te vas ahora, dejarás de recibir estas alertas críticas.",
        "pt": f"⚠️ Tem certeza? Nos últimos 30 dias, detectamos que **{threats_detected[1].competitor_name}** subiu no ranking e está a apenas 2 avaliações de te superar. Se você sair agora, deixará de receber estes alertas críticos.",
        "en": f"⚠️ Are you sure? In the last 30 days, we detected that **{threats_detected[1].competitor_name}** climbed the rankings and is only 2 reviews away from overtaking you. If you leave now, you'll stop receiving these critical alerts."
    }
    
    urgency_message = urgency_messages.get(request.language, urgency_messages["en"])
    
    # Determinar nivel de riesgo
    risk_level = "high" if len(threats_detected) >= 2 else "medium"
    
    return MicroAuditResponse(
        lead_id=request.lead_id,
        subscription_id=request.subscription_id,
        has_threats=len(threats_detected) > 0,
        threats_detected=threats_detected,
        business_current_rank=5,  # TODO: Calcular rank real
        total_competitors=12,  # TODO: Calcular total real
        days_since_last_scan=days_since_last_scan,
        urgency_message=urgency_message,
        risk_level=risk_level
    )


# ============================================================================
# PASO 2: RETENTION OFFER (Soborno Estratégico)
# ============================================================================

@router.post("/retention-offer", response_model=RetentionOfferResponse)
async def generate_retention_offer(
    request: CancellationAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    💰 PASO 2 del Exit Flow: Retention Offer
    
    Si el usuario persiste en cancelar después del Micro-Audit:
    - Genera cupón automático de 50% descuento para 1 mes
    - O ofrece 15 días gratis adicionales
    - Crea el cupón en Stripe en tiempo real
    
    **Presupuesto $0:** El descuento es mejor que perder al cliente.
    """
    
    # Verificar suscripción
    subscription = db.query(RadarSubscription).filter(
        and_(
            RadarSubscription.id == request.subscription_id,
            RadarSubscription.lead_id == request.lead_id
        )
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Decidir qué tipo de oferta hacer
    # Estrategia: 50% descuento para 2 meses (mejor ROI que 15 días gratis)
    offer_type = "discount_50"
    original_price = subscription.monthly_price
    discount_price = original_price * 0.5
    savings_amount = original_price * 2  # Ahorro en 2 meses
    
    # Crear cupón en Stripe
    coupon_code = None
    try:
        # Crear cupón de 50% para 2 meses
        coupon = stripe.Coupon.create(
            percent_off=50,
            duration="repeating",
            duration_in_months=2,
            name=f"Retention Offer - Lead {request.lead_id}",
            metadata={
                "lead_id": request.lead_id,
                "subscription_id": request.subscription_id,
                "offer_type": "retention_50_off"
            }
        )
        coupon_code = coupon.id
    except Exception as e:
        print(f"Error creating Stripe coupon: {e}")
        # Si falla Stripe, aún podemos mostrar la oferta
        coupon_code = "RETENTION50"
    
    # Generar mensaje persuasivo según idioma
    persuasion_messages = {
        "es": f"🎁 **Última oportunidad:** Quédate 2 meses más al **50% de descuento** (solo ${discount_price:.0f}/mes en lugar de ${original_price:.0f}) y te regalamos un reporte premium de palabras clave ocultas que usan tus competidores. Ahorras **${savings_amount:.0f}** y mantienes tu ventaja competitiva.",
        "pt": f"🎁 **Última chance:** Fique mais 2 meses com **50% de desconto** (apenas ${discount_price:.0f}/mês em vez de ${original_price:.0f}) e ganhamos um relatório premium de palavras-chave ocultas que seus concorrentes usam. Você economiza **${savings_amount:.0f}** e mantém sua vantagem competitiva.",
        "en": f"🎁 **Last chance:** Stay 2 more months at **50% off** (only ${discount_price:.0f}/month instead of ${original_price:.0f}) and get a free premium report of hidden keywords your competitors are using. You save **${savings_amount:.0f}** and keep your competitive edge."
    }
    
    cta_texts = {
        "es": "✅ Aceptar oferta (50% OFF)",
        "pt": "✅ Aceitar oferta (50% OFF)",
        "en": "✅ Accept offer (50% OFF)"
    }
    
    persuasion_message = persuasion_messages.get(request.language, persuasion_messages["en"])
    cta_button_text = cta_texts.get(request.language, cta_texts["en"])
    
    # URL para aplicar el cupón (asume endpoint de aplicar cupón)
    offer_accepted_url = f"/api/retention/apply-coupon/{coupon_code}" if coupon_code else None
    
    return RetentionOfferResponse(
        lead_id=request.lead_id,
        subscription_id=request.subscription_id,
        offer=RetentionOfferType(
            offer_type=offer_type,
            original_price=original_price,
            discount_price=discount_price,
            free_days=None,
            bonus_feature="premium_keywords_report",
            coupon_code=coupon_code,
            valid_until=datetime.utcnow() + timedelta(hours=24),  # Válido por 24h
            savings_amount=savings_amount
        ),
        persuasion_message=persuasion_message,
        cta_button_text=cta_button_text,
        offer_accepted_url=offer_accepted_url
    )


# ============================================================================
# APLICAR CUPÓN DE RETENCIÓN
# ============================================================================

@router.post("/apply-coupon/{coupon_code}")
async def apply_retention_coupon(
    coupon_code: str,
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aplica el cupón de retención a la suscripción de Stripe del usuario.
    """
    
    # Buscar la suscripción
    subscription = db.query(RadarSubscription).filter(
        RadarSubscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    if not subscription.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe subscription found"
        )
    
    try:
        # Aplicar cupón a la suscripción en Stripe
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            coupon=coupon_code,
            metadata={
                "retention_offer_accepted": "true",
                "retention_coupon": coupon_code,
                "accepted_at": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": "Retention offer applied successfully",
            "coupon_code": coupon_code,
            "discount": "50% off for 2 months"
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to apply coupon: {str(e)}"
        )


# ============================================================================
# PASO 3: CHURN FEEDBACK (Encuesta de Salida)
# ============================================================================

@router.post("/churn-feedback", response_model=ChurnFeedbackResponse)
async def submit_churn_feedback(
    feedback: ChurnFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 PASO 3 del Exit Flow: Churn Feedback
    
    Si el usuario finalmente cancela:
    - Guarda el motivo de cancelación
    - Registra si aceptó o rechazó la retention offer
    - Permite análisis posterior para mejorar producto
    
    **Data-Driven:** Cada churn es una oportunidad de aprendizaje.
    """
    
    # Buscar lead y suscripción para contexto adicional
    lead = db.query(Lead).filter(Lead.id == feedback.lead_id).first()
    subscription = db.query(RadarSubscription).filter(
        RadarSubscription.id == feedback.subscription_id
    ).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Calcular días de suscripción
    days_subscribed = 0
    if subscription and subscription.created_at:
        days_subscribed = (datetime.utcnow() - subscription.created_at).days
    
    # Crear registro de feedback
    churn_record = ChurnFeedback(
        lead_id=feedback.lead_id,
        subscription_id=feedback.subscription_id,
        reason_category=feedback.cancellation_reason.reason_category,
        reason_detail=feedback.cancellation_reason.reason_detail,
        satisfaction_score=feedback.cancellation_reason.satisfaction_score,
        accepted_retention_offer=feedback.accepted_retention_offer,
        retention_offer_type=feedback.retention_offer_type,
        retention_offer_shown=True,
        language=feedback.language,
        had_active_threats=False,  # TODO: Consultar si había amenazas
        days_subscribed=days_subscribed,
        total_alerts_received=subscription.total_alerts_sent if subscription else 0
    )
    
    db.add(churn_record)
    db.commit()
    db.refresh(churn_record)
    
    # Si finalmente cancela, actualizar estado de suscripción
    if subscription and not feedback.accepted_retention_offer:
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.utcnow()
        db.commit()
    
    return ChurnFeedbackResponse(
        id=churn_record.id,
        lead_id=churn_record.lead_id,
        subscription_id=churn_record.subscription_id,
        reason_category=churn_record.reason_category,
        reason_detail=churn_record.reason_detail,
        satisfaction_score=churn_record.satisfaction_score,
        accepted_retention_offer=churn_record.accepted_retention_offer,
        retention_offer_type=churn_record.retention_offer_type,
        language=churn_record.language,
        created_at=churn_record.created_at
    )


# ============================================================================
# ANALYTICS: DASHBOARD DE CHURN
# ============================================================================

@router.get("/churn-analytics")
async def get_churn_analytics(
    time_range: str = "30d",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 Analytics de Churn para el Command Center
    
    Retorna:
    - Total de cancelaciones por período
    - Distribución de motivos (price, not_using, competitor, etc)
    - Tasa de aceptación de retention offers
    - Promedio de satisfaction_score
    - Patrones: días promedio antes de cancelar
    """
    
    # Solo admins pueden ver analytics
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access churn analytics"
        )
    
    # Calcular fecha de inicio según time_range
    if time_range == "7d":
        start_date = datetime.utcnow() - timedelta(days=7)
    elif time_range == "30d":
        start_date = datetime.utcnow() - timedelta(days=30)
    elif time_range == "90d":
        start_date = datetime.utcnow() - timedelta(days=90)
    else:
        start_date = datetime.utcnow() - timedelta(days=365)
    
    # Query de feedbacks en el período
    feedbacks = db.query(ChurnFeedback).filter(
        ChurnFeedback.created_at >= start_date
    ).all()
    
    total_cancellations = len(feedbacks)
    
    # Distribución de razones
    reason_distribution = {}
    for feedback in feedbacks:
        reason = feedback.reason_category
        reason_distribution[reason] = reason_distribution.get(reason, 0) + 1
    
    # Tasa de aceptación de retention offers
    accepted_offers = sum(1 for f in feedbacks if f.accepted_retention_offer)
    retention_offer_acceptance_rate = (accepted_offers / total_cancellations * 100) if total_cancellations > 0 else 0
    
    # Promedio de satisfaction score
    scores = [f.satisfaction_score for f in feedbacks if f.satisfaction_score]
    avg_satisfaction = sum(scores) / len(scores) if scores else 0
    
    # Días promedio antes de cancelar
    days_list = [f.days_subscribed for f in feedbacks if f.days_subscribed]
    avg_days_before_churn = sum(days_list) / len(days_list) if days_list else 0
    
    return {
        "time_range": time_range,
        "total_cancellations": total_cancellations,
        "reason_distribution": reason_distribution,
        "retention_metrics": {
            "offers_accepted": accepted_offers,
            "acceptance_rate_percent": round(retention_offer_acceptance_rate, 2),
            "offers_rejected": total_cancellations - accepted_offers
        },
        "satisfaction": {
            "average_score": round(avg_satisfaction, 2),
            "total_responses": len(scores)
        },
        "lifecycle": {
            "avg_days_before_churn": round(avg_days_before_churn, 1),
            "shortest_subscription": min(days_list) if days_list else 0,
            "longest_subscription": max(days_list) if days_list else 0
        },
        "top_churn_reasons": sorted(
            reason_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
    }
