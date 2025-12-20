from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum as SQLEnum, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class PaymentStatus(str, enum.Enum):
    """Estados del pago"""
    PENDING = "pending"
    PAID = "paid"
    DELIVERED = "delivered"
    FAILED = "failed"


class CustomerStatus(str, enum.Enum):
    """Estados del cliente"""
    LEAD = "lead"  # Solo dejó datos
    CLIENTE = "cliente"  # Pagó algún producto


class ProductType(str, enum.Enum):
    """Tipos de productos"""
    EBOOK = "ebook"  # E-book $9
    SERVICE = "service"  # Servicio completo $99


class OrderStatus(str, enum.Enum):
    """Estados de la orden"""
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"


class Lead(Base):
    """Modelo de Lead - Usuario que completa el formulario"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    
    # Información de contacto (campos esenciales)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, nullable=False)
    whatsapp = Column(String, nullable=True)  # Número de WhatsApp
    
    # Datos del negocio auditado
    nombre_negocio = Column(String, nullable=False, index=True)  # business_name
    
    # Resultados de la auditoría
    score_visibilidad = Column(Integer)  # initial_score (0-100)
    fallos_criticos = Column(JSON)  # Guardamos el JSON con los fallos
    audit_data = Column(JSON)  # Datos completos de la auditoría
    
    # Estado del cliente
    customer_status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.LEAD)
    
    # Stripe
    stripe_customer_id = Column(String, nullable=True, index=True)  # ID de cliente en Stripe
    stripe_checkout_session_id = Column(String, nullable=True)  # Última sesión de checkout
    stripe_payment_intent_id = Column(String, nullable=True)  # Último payment intent
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)  # Fecha del primer pago
    
    # Relaciones
    orders = relationship("Order", back_populates="lead")

    def __repr__(self):
        return f"<Lead {self.email} - {self.nombre_negocio} - {self.customer_status}>"


class Order(Base):
    """Modelo de Orden - Registro de compras"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con el lead
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", back_populates="orders")
    
    # Información del producto
    product_type = Column(SQLEnum(ProductType), nullable=False, index=True)  # 'ebook' o 'service'
    amount = Column(Float, nullable=False)  # Monto pagado en USD
    currency = Column(String, default="usd")
    
    # Información de Stripe
    stripe_session_id = Column(String, unique=True, nullable=False, index=True)
    stripe_payment_intent_id = Column(String, nullable=True, index=True)
    
    # Estado de la orden: pending -> paid -> completed
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, index=True)
    
    # Entregables
    download_link = Column(String, nullable=True)  # Link de descarga del e-book
    notes = Column(Text, nullable=True)  # Notas para el equipo de trabajo
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Order {self.id} - {self.product_type} - {self.status}>"
