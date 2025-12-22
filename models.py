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


class TaskCategory(str, enum.Enum):
    """Categorías de tareas"""
    SEO = "seo"  # Tareas de optimización SEO
    CONTENIDO = "contenido"  # Creación de contenido, fotos, etc.
    VERIFICACION = "verificacion"  # Revisión y verificación de cambios


class UserRole(str, enum.Enum):
    """Roles de usuarios del backoffice"""
    SUPERUSER = "superuser"  # Acceso total al dashboard
    WORKER = "worker"  # Solo acceso al Work Queue


class SubscriptionStatus(str, enum.Enum):
    """Estados de suscripción Radar Lokigi"""
    ACTIVE = "active"  # Activa y pagando
    TRIAL = "trial"  # Período de prueba
    CANCELLED = "cancelled"  # Cancelada por el usuario
    EXPIRED = "expired"  # Expirada por falta de pago
    PAUSED = "paused"  # Pausada temporalmente


class User(Base):
    """Modelo de Usuario del Backoffice"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.WORKER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)


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
    
    # Suscripción Premium
    premium_subscriber = Column(Boolean, default=False, nullable=False)  # Flag para suscriptores $29/mes
    subscription_id = Column(String, nullable=True, index=True)  # ID de suscripción en Stripe
    subscription_status = Column(String, nullable=True)  # active, canceled, past_due, etc.
    subscription_current_period_end = Column(DateTime(timezone=True), nullable=True)  # Fin del período actual
    
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
    
    # Relación con tareas
    tasks = relationship("Task", back_populates="order", cascade="all, delete-orphan")
    
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
    
    # Relaciones
    tasks = relationship("Task", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order {self.id} - {self.product_type} - {self.status}>"


class Task(Base):
    """Modelo de Tarea - Tareas operativas para completar órdenes"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con la orden
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    order = relationship("Order", back_populates="tasks")
    
    # Información de la tarea
    description = Column(Text, nullable=False)  # Descripción de la tarea
    category = Column(SQLEnum(TaskCategory), nullable=False, index=True)  # Categoría de la tarea
    is_completed = Column(Boolean, default=False, index=True)  # Estado de completado
    
    # Prioridad y orden
    priority = Column(Integer, default=0)  # Mayor número = mayor prioridad
    order_index = Column(Integer, default=0)  # Orden de visualización
    
    # Notas adicionales
    notes = Column(Text, nullable=True)  # Notas del equipo sobre esta tarea
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)  # Cuándo se completó
    
    def __repr__(self):
        return f"<Task {self.id} - {self.category} - {'✓' if self.is_completed else '○'}>"


class DataQualityEvaluation(Base):
    """Modelo de Evaluación de Calidad de Datos - NAP Consistency"""
    __tablename__ = "data_quality_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con el lead
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True, unique=True)
    
    # Score global de integridad (0-100)
    overall_score = Column(Float, nullable=False, index=True)
    
    # Scores por dimensión
    name_consistency_score = Column(Float, nullable=True)
    phone_consistency_score = Column(Float, nullable=True)
    address_consistency_score = Column(Float, nullable=True)
    location_accuracy_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    
    # Datos detallados de la evaluación (JSON)
    evaluation_data = Column(JSON, nullable=False)  # Resultados completos de NAPEvaluator
    
    # Alertas críticas detectadas
    alerts = Column(JSON, nullable=True)  # Lista de alertas
    
    # Recomendaciones generadas
    recommendations = Column(JSON, nullable=True)  # Lista de recomendaciones
    
    # Flag: ¿Requiere servicio de limpieza? (score < 90%)
    requires_cleanup_service = Column(Boolean, default=False, index=True)
    
    # Plataformas evaluadas
    platforms_evaluated = Column(JSON, nullable=True)  # ["google_maps", "facebook", "instagram", "website"]
    
    # Estado de la evaluación
    status = Column(String, default="completed")  # completed, pending, error
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<DataQualityEvaluation Lead:{self.lead_id} Score:{self.overall_score}% {'⚠️ Cleanup Required' if self.requires_cleanup_service else '✓'}>"


class CompetitorSnapshot(Base):
    """Modelo de Snapshot de Competidor - Histórico mensual de métricas de competidores"""
    __tablename__ = "competitor_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con el lead (el negocio que está monitoreando)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Identificación del competidor
    competitor_name = Column(String, nullable=False, index=True)
    competitor_place_id = Column(String, nullable=True, index=True)  # Google Place ID si está disponible
    
    # Métricas del competidor en este snapshot
    score = Column(Float, nullable=False)  # Score de visibilidad (0-100)
    rating = Column(Float, nullable=True)  # Rating de Google (0-5)
    review_count = Column(Integer, nullable=True)  # Número de reseñas
    photo_count = Column(Integer, nullable=True)  # Número de fotos
    has_website = Column(Boolean, nullable=True)
    
    # Datos completos del snapshot (JSON)
    snapshot_data = Column(JSON, nullable=False)  # Todos los datos del competidor
    
    # Cambios detectados vs snapshot anterior
    changes_detected = Column(JSON, nullable=True)  # {"score_delta": +5, "review_delta": +10, etc.}
    
    # Tipo de snapshot
    snapshot_type = Column(String, default="monthly")  # monthly, manual, alert_triggered
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CompetitorSnapshot {self.competitor_name} Lead:{self.lead_id} Score:{self.score}>"


class RadarAlert(Base):
    """Modelo de Alerta de Radar - Alertas generadas por movimientos de competidores"""
    __tablename__ = "radar_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con el lead (el cliente que recibe la alerta)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Tipo de alerta
    alert_type = Column(String, nullable=False, index=True)  # competitor_movement, market_shift, position_risk
    severity = Column(String, nullable=False, index=True)  # critical, warning, info
    
    # Competidor que generó la alerta
    competitor_name = Column(String, nullable=True)
    competitor_snapshot_id = Column(Integer, ForeignKey("competitor_snapshots.id"), nullable=True)
    
    # Contenido de la alerta
    title = Column(String, nullable=False)  # "Alerta Lokigi: [Competidor X] se está moviendo"
    message = Column(Text, nullable=False)  # Descripción detallada
    
    # Métricas que dispararon la alerta
    trigger_data = Column(JSON, nullable=True)  # {"score_increase": 5, "new_reviews": 10, etc.}
    
    # Recomendaciones para el cliente
    recommendations = Column(JSON, nullable=True)  # Lista de acciones sugeridas
    
    # Estado de la alerta
    status = Column(String, default="pending", index=True)  # pending, sent, read, dismissed
    
    # Notificación enviada
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    notification_channels = Column(JSON, nullable=True)  # ["email", "whatsapp"]
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<RadarAlert [{self.severity}] {self.title} Lead:{self.lead_id}>"


class VisibilityHeatmap(Base):
    """Modelo de Mapa de Calor de Visibilidad - Snapshots mensuales del área de influencia"""
    __tablename__ = "visibility_heatmaps"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con el lead
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Datos del heatmap
    center_coordinates = Column(JSON, nullable=False)  # [lat, lng] del negocio
    radius_meters = Column(Float, nullable=False)  # Radio de influencia calculado
    
    # Métricas de visibilidad por zona
    visibility_zones = Column(JSON, nullable=False)  # Grid de zonas con scores de visibilidad
    
    # Competidores en el área
    competitors_in_area = Column(JSON, nullable=False)  # Lista de competidores con coordenadas
    competitor_density = Column(Float, nullable=True)  # Competidores por km²
    
    # Score global del área
    area_dominance_score = Column(Float, nullable=False)  # 0-100: Qué tan dominante es el negocio en su área
    
    # Comparación con período anterior
    previous_heatmap_id = Column(Integer, ForeignKey("visibility_heatmaps.id"), nullable=True)
    area_growth_percent = Column(Float, nullable=True)  # % de crecimiento/reducción del área de influencia
    dominance_change = Column(Float, nullable=True)  # Cambio en dominance score
    
    # Datos completos del heatmap (JSON)
    heatmap_data = Column(JSON, nullable=False)  # Datos para renderizar el mapa
    
    # Tipo de snapshot
    snapshot_type = Column(String, default="monthly")  # monthly, manual
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<VisibilityHeatmap Lead:{self.lead_id} Dominance:{self.area_dominance_score}% Growth:{self.area_growth_percent}%>"


class RadarSubscription(Base):
    """Modelo de Suscripción a Radar Lokigi ($29/mes)"""
    __tablename__ = "radar_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con el lead
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True, unique=True)
    lead = relationship("Lead", backref="radar_subscription")
    
    # Estado de la suscripción
    status = Column(SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIAL)
    
    # Datos de pago
    stripe_subscription_id = Column(String, nullable=True, index=True)  # ID de Stripe Subscription
    stripe_customer_id = Column(String, nullable=True)  # ID del customer en Stripe
    
    # Precios y billing
    monthly_price = Column(Float, default=29.0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    
    # Fechas importantes
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuración del radar
    competitors_to_track = Column(JSON, nullable=False, default=[])  # Lista de IDs de competidores
    monitoring_frequency_days = Column(Integer, default=30, nullable=False)  # Frecuencia de monitoreo
    last_monitoring_at = Column(DateTime(timezone=True), nullable=True)
    next_monitoring_at = Column(DateTime(timezone=True), nullable=True)
    
    # Alertas
    alerts_enabled = Column(Boolean, default=True, nullable=False)
    alert_email = Column(String, nullable=True)
    alert_phone = Column(String, nullable=True)  # Para WhatsApp
    
    # Métricas de uso
    total_alerts_sent = Column(Integer, default=0, nullable=False)
    total_heatmaps_generated = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<RadarSubscription Lead:{self.lead_id} Status:{self.status} Price:${self.monthly_price}>"


class CompetitorSnapshot(Base):
    """Modelo de Snapshot de Competidor - Estado en un momento específico"""
    __tablename__ = "competitor_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con el competidor (Lead)
    competitor_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    # Relación con la suscripción que lo monitorea
    subscription_id = Column(Integer, ForeignKey("radar_subscriptions.id"), nullable=False, index=True)
    
    # Datos del snapshot
    name = Column(String, nullable=False)
    rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, nullable=True)
    photos_count = Column(Integer, nullable=True)
    response_rate = Column(Float, nullable=True)  # % de respuestas a reseñas
    
    # Score calculado
    visibility_score = Column(Float, nullable=True)  # Score de visibilidad 0-100
    
    # Datos completos del competidor
    snapshot_data = Column(JSON, nullable=False)  # Datos completos en JSON
    
    # Comparación con snapshot anterior
    previous_snapshot_id = Column(Integer, ForeignKey("competitor_snapshots.id"), nullable=True)
    rating_change = Column(Float, nullable=True)
    reviews_change = Column(Integer, nullable=True)
    photos_change = Column(Integer, nullable=True)
    score_change = Column(Float, nullable=True)
    
    # Alertas generadas
    alert_triggered = Column(Boolean, default=False, nullable=False)
    alert_reasons = Column(JSON, nullable=True)  # Lista de razones por las que se disparó alerta
    
    # Timestamps
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CompetitorSnapshot {self.name} Score:{self.visibility_score} Change:{self.score_change}>"

