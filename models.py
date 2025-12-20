from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from database import Base
import enum


class PaymentStatus(str, enum.Enum):
    """Estados del pago"""
    PENDING = "pending"
    PAID = "paid"
    DELIVERED = "delivered"
    FAILED = "failed"


class Lead(Base):
    """Modelo de Lead - Usuario que completa el formulario"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, nullable=False)
    
    # Datos del negocio auditado
    nombre_negocio = Column(String, nullable=False)
    rating = Column(Float)
    numero_resenas = Column(Integer)
    tiene_sitio_web = Column(Boolean, default=False)
    fecha_ultima_foto = Column(String)
    
    # Resultados de la auditoría
    score_visibilidad = Column(Integer)
    fallos_criticos = Column(JSON)  # Guardamos el JSON con los fallos
    
    # Estado del pago
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    stripe_payment_intent_id = Column(String, nullable=True)
    stripe_checkout_session_id = Column(String, nullable=True)
    
    # Ofertas
    oferta_plan_express = Column(Boolean, default=False)  # Si se le ofreció el plan
    plan_express_accepted = Column(Boolean, default=False)  # Si lo aceptó
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Lead {self.email} - {self.nombre_negocio} - {self.payment_status}>"
