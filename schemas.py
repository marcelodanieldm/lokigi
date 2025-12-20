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
