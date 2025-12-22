from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import PaymentStatus


class LeadCreate(BaseModel):
    """Datos para crear un lead"""
    email: EmailStr
    telefono: str
    nombre_negocio: str


class FalloCriticoSchema(BaseModel):
    """Esquema de un fallo crítico"""
    titulo: str
    descripcion: str
    impacto_economico: str


class AuditReportSchema(BaseModel):
    """Esquema del reporte de auditoría"""
    fallos_criticos: List[FalloCriticoSchema]
    score_visibilidad: int


class LeadResponse(BaseModel):
    """Respuesta con datos del lead"""
    id: int
    email: str
    telefono: str
    nombre_negocio: str
    score_visibilidad: Optional[int]
    payment_status: PaymentStatus
    oferta_plan_express: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    """Respuesta para iniciar checkout de Stripe"""
    checkout_url: str
    session_id: str


class StripeWebhookEvent(BaseModel):
    """Datos del webhook de Stripe"""
    type: str
    data: dict


# ===== DATA QUALITY SCHEMAS =====

class PlatformNAPData(BaseModel):
    """Datos NAP de una plataforma específica"""
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class DataQualityEvaluationRequest(BaseModel):
    """Request para evaluar calidad de datos NAP"""
    lead_id: int
    
    # Datos de Google Maps (source of truth)
    google_maps_data: PlatformNAPData
    google_maps_coordinates: Optional[List[float]] = None  # [lat, lng]
    
    # Datos de otras plataformas (opcionales)
    facebook_data: Optional[PlatformNAPData] = None
    instagram_data: Optional[PlatformNAPData] = None
    website_data: Optional[PlatformNAPData] = None
    
    # Coordenadas geocodificadas de la dirección
    address_coordinates: Optional[List[float]] = None  # [lat, lng]
    
    # Datos adicionales de Google Maps para completitud
    google_maps_extras: Optional[dict] = None  # business_hours, menu_url, etc.


class DimensionScore(BaseModel):
    """Score de una dimensión específica"""
    score: float
    status: str
    details: Optional[dict] = None


class DataQualityAlert(BaseModel):
    """Alerta de calidad de datos"""
    type: str  # "critical", "warning"
    title: str
    message: str
    priority: int


class DataQualityEvaluationResponse(BaseModel):
    """Respuesta de evaluación de calidad de datos"""
    lead_id: int
    overall_score: float
    
    # Scores por dimensión
    name_consistency: DimensionScore
    phone_consistency: DimensionScore
    address_consistency: DimensionScore
    location_accuracy: DimensionScore
    completeness: DimensionScore
    
    # Alertas y recomendaciones
    alerts: List[DataQualityAlert]
    recommendations: List[str]
    
    # ¿Requiere servicio de limpieza?
    requires_cleanup_service: bool
    
    # Plataformas evaluadas
    platforms_evaluated: List[str]
    
    # Timestamp
    evaluated_at: datetime
    
    class Config:
        from_attributes = True


class DataQualityReportSummary(BaseModel):
    """Resumen de evaluación para dashboard"""
    lead_id: int
    business_name: str
    overall_score: float
    requires_cleanup_service: bool
    critical_alerts_count: int
    evaluated_at: datetime


# ===== RADAR LOKIGI SCHEMAS =====

class CompetitorSnapshotCreate(BaseModel):
    """Request para crear snapshot de competidor"""
    lead_id: int
    competitor_name: str
    competitor_data: dict  # Datos completos del competidor


class CompetitorSnapshotResponse(BaseModel):
    """Respuesta de snapshot de competidor"""
    id: int
    lead_id: int
    competitor_name: str
    score: float
    rating: Optional[float]
    review_count: Optional[int]
    photo_count: Optional[int]
    has_website: Optional[bool]
    changes_detected: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CompetitorHistoryResponse(BaseModel):
    """Histórico de un competidor"""
    competitor_name: str
    snapshots: List[dict]  # Lista de snapshots ordenados cronológicamente
    total_snapshots: int


class RadarAlertResponse(BaseModel):
    """Respuesta de alerta de Radar"""
    id: int
    lead_id: int
    alert_type: str
    severity: str
    competitor_name: Optional[str]
    title: str
    message: str
    trigger_data: Optional[dict]
    recommendations: Optional[List[str]]
    status: str
    notification_sent: bool
    notification_sent_at: Optional[datetime]
    created_at: datetime
    read_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class VisibilityHeatmapResponse(BaseModel):
    """Respuesta de mapa de calor de visibilidad"""
    id: int
    lead_id: int
    center_coordinates: List[float]  # [lat, lng]
    radius_meters: float
    area_dominance_score: float
    competitor_density: Optional[float]
    area_growth_percent: Optional[float]
    dominance_change: Optional[float]
    heatmap_data: dict  # Datos completos para renderizar
    created_at: datetime
    
    class Config:
        from_attributes = True


class RadarScanRequest(BaseModel):
    """Request para escanear competidores"""
    lead_id: int
    competitors_data: List[dict]  # Lista de datos de competidores
    business_coordinates: Optional[List[float]] = None  # [lat, lng]
    business_score: Optional[float] = None


class RadarScanResponse(BaseModel):
    """Respuesta de scan de Radar"""
    lead_id: int
    scan_timestamp: datetime
    competitors_scanned: int
    movements_detected: int
    alerts_generated: int
    scan_results: List[dict]


class CompetitorComparisonResponse(BaseModel):
    """Comparación de competidores"""
    business_score: float
    business_rank: int  # Posición en el ranking
    total_competitors: int
    competitors: List[dict]  # Lista ordenada por score


class RadarStatusResponse(BaseModel):
    """Estado del monitoreo de Radar"""
    lead_id: int
    is_premium_subscriber: bool
    last_scan_date: Optional[datetime]
    next_scan_date: Optional[datetime]
    total_competitors_tracked: int
    pending_alerts: int
    latest_heatmap_date: Optional[datetime]


# ============================================================================
# SCHEMAS PARA RADAR LOKIGI SUBSCRIPTION ($29/mes)
# ============================================================================

class RadarSubscriptionCreate(BaseModel):
    """Crear suscripción Radar"""
    lead_id: int
    competitor_ids: List[int]
    alert_email: Optional[str] = None
    alert_phone: Optional[str] = None


class RadarSubscriptionResponse(BaseModel):
    """Respuesta de suscripción Radar"""
    id: int
    lead_id: int
    status: str
    monthly_price: float
    currency: str
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    competitors_to_track: List[int]
    monitoring_frequency_days: int
    last_monitoring_at: Optional[datetime]
    next_monitoring_at: Optional[datetime]
    alerts_enabled: bool
    total_alerts_sent: int
    total_heatmaps_generated: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CompetitorSnapshotResponse(BaseModel):
    """Snapshot de competidor"""
    id: int
    competitor_id: int
    subscription_id: int
    name: str
    rating: Optional[float]
    reviews_count: Optional[int]
    photos_count: Optional[int]
    visibility_score: Optional[float]
    rating_change: Optional[float]
    reviews_change: Optional[int]
    photos_change: Optional[int]
    score_change: Optional[float]
    alert_triggered: bool
    alert_reasons: Optional[List[dict]]
    captured_at: datetime
    
    class Config:
        from_attributes = True


class MonitoringResultResponse(BaseModel):
    """Resultado de monitoreo"""
    subscription_id: int
    lead_id: int
    monitored_at: str
    competitors_checked: int
    snapshots_created: int
    alerts_generated: int
    snapshots: List[dict]
    alerts: List[dict]


class VisibilityHeatmapResponse(BaseModel):
    """Respuesta de heatmap de visibilidad"""
    id: int
    lead_id: int
    center_coordinates: List[float]
    radius_meters: float
    visibility_zones: dict
    competitors_in_area: List[dict]
    competitor_density: Optional[float]
    area_dominance_score: float
    area_growth_percent: Optional[float]
    dominance_change: Optional[float]
    heatmap_data: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS PARA EXIT FLOW ANTI-CHURN (Escudo de Retención)
# ============================================================================

class CancellationAttemptRequest(BaseModel):
    """Request cuando usuario intenta cancelar suscripción"""
    lead_id: int
    subscription_id: int
    language: str  # "es", "pt", "en"


class CompetitorThreat(BaseModel):
    """Amenaza de competidor detectada en micro-audit"""
    competitor_name: str
    threat_type: str  # "ranking_increase", "reviews_surge", "score_jump"
    threat_level: str  # "critical", "high", "medium"
    details: str  # Descripción del peligro
    metric_change: dict  # {"reviews": +5, "rating": +0.3, etc}


class MicroAuditResponse(BaseModel):
    """Respuesta del micro-audit al intentar cancelar"""
    lead_id: int
    subscription_id: int
    has_threats: bool
    threats_detected: List[CompetitorThreat]
    business_current_rank: int
    total_competitors: int
    days_since_last_scan: int
    urgency_message: str  # Mensaje dinámico en idioma del usuario
    risk_level: str  # "high", "medium", "low"


class RetentionOfferType(BaseModel):
    """Tipo de oferta de retención"""
    offer_type: str  # "discount_50", "free_15_days", "premium_report"
    original_price: float
    discount_price: Optional[float]
    free_days: Optional[int]
    bonus_feature: Optional[str]
    coupon_code: Optional[str]  # Código de Stripe
    valid_until: datetime
    savings_amount: float


class RetentionOfferResponse(BaseModel):
    """Respuesta con oferta de retención"""
    lead_id: int
    subscription_id: int
    offer: RetentionOfferType
    persuasion_message: str  # Mensaje en idioma del usuario
    cta_button_text: str  # "Aceptar oferta", "Accept offer", etc
    offer_accepted_url: Optional[str]  # URL para aplicar cupón


class ChurnReason(BaseModel):
    """Motivo de cancelación"""
    reason_category: str  # "price", "not_using", "missing_features", "competitor", "other"
    reason_detail: Optional[str]  # Texto libre del usuario
    satisfaction_score: Optional[int]  # 1-5


class ChurnFeedbackCreate(BaseModel):
    """Request para guardar feedback de churn"""
    lead_id: int
    subscription_id: int
    cancellation_reason: ChurnReason
    accepted_retention_offer: bool
    retention_offer_type: Optional[str]
    language: str


class ChurnFeedbackResponse(BaseModel):
    """Respuesta de feedback guardado"""
    id: int
    lead_id: int
    subscription_id: int
    reason_category: str
    reason_detail: Optional[str]
    satisfaction_score: Optional[int]
    accepted_retention_offer: bool
    retention_offer_type: Optional[str]
    language: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CancellationFlowStatus(BaseModel):
    """Estado del flujo de cancelación"""
    step: int  # 1 = micro-audit, 2 = retention offer, 3 = feedback
    can_proceed_to_cancel: bool
    retention_offer_shown: bool
    feedback_submitted: bool

