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
