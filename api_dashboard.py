"""
Dashboard API - Endpoints para el panel operativo del equipo
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime
import io
import zipfile
import tempfile
import os

from database import get_db
from models import Order, Lead, ProductType, OrderStatus, Task, TaskCategory
from task_generator import (
    generate_tasks_from_audit,
    get_task_completion_percentage,
    mark_task_completed,
    mark_task_incomplete
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# Schemas
class OrderListItem(BaseModel):
    """Schema para item de la lista de órdenes"""
    id: int
    lead_id: int
    client_name: str
    client_email: str
    client_phone: str
    client_whatsapp: Optional[str]
    business_name: str
    amount: float
    status: str
    score_inicial: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    pais: Optional[str]  # Código de país (BR, US, ES, etc.)
    idioma: Optional[str]  # Código de idioma (pt, en, es)
    
    class Config:
        from_attributes = True


class ChecklistItem(BaseModel):
    """Item del checklist"""
    id: str
    text: str
    completed: bool


class OrderDetailResponse(BaseModel):
    """Schema detallado de una orden"""
    id: int
    lead_id: int
    
    # Datos del cliente
    client_name: str
    client_email: str
    client_phone: str
    client_whatsapp: Optional[str]
    business_name: str
    
    # Datos de la orden
    amount: float
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    notes: Optional[str]
    
    # Datos de auditoría
    score_inicial: Optional[int]
    fallos_criticos: Optional[dict]
    audit_data: Optional[dict]
    
    # Checklist (se genera dinámicamente)
    checklist: List[ChecklistItem]
    
    class Config:
        from_attributes = True


class UpdateOrderStatusRequest(BaseModel):
    """Request para actualizar estado de orden"""
    status: str  # PENDING, IN_PROGRESS, COMPLETED


class CompleteOrderRequest(BaseModel):
    """Request para marcar orden como completada"""
    notes: Optional[str] = None


class DashboardStats(BaseModel):
    """Estadísticas del dashboard"""
    total_orders: int
    pending_orders: int
    in_progress_orders: int
    completed_orders: int
    total_revenue: float


class TaskResponse(BaseModel):
    """Schema de respuesta para una tarea"""
    id: int
    order_id: int
    description: str
    category: str
    is_completed: bool
    priority: int
    order_index: int
    notes: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UpdateTaskRequest(BaseModel):
    """Request para actualizar una tarea"""
    is_completed: bool
    notes: Optional[str] = None


class TaskListResponse(BaseModel):
    """Lista de tareas de una orden"""
    tasks: List[TaskResponse]
    completion_percentage: float
    pending_tasks: int


# Endpoints
@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas generales del dashboard
    """
    # Contar órdenes de servicio ($99)
    all_orders = db.query(Order).filter(Order.product_type == ProductType.SERVICE).all()
    
    stats = {
        "total_orders": len(all_orders),
        "pending_orders": len([o for o in all_orders if o.status == OrderStatus.PENDING]),
        "in_progress_orders": len([o for o in all_orders if o.status == OrderStatus.IN_PROGRESS]),
        "completed_orders": len([o for o in all_orders if o.status == OrderStatus.COMPLETED]),
        "total_revenue": sum(o.amount for o in all_orders if o.status == OrderStatus.COMPLETED)
    }
    
    return stats


@router.get("/orders", response_model=List[OrderListItem])
async def get_orders(
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene lista de órdenes de servicio ($99)
    
    Parámetros:
    - status_filter: Filtrar por estado (PENDING, IN_PROGRESS, COMPLETED)
    - search: Buscar por nombre de negocio o cliente
    """
    # Query base: solo órdenes de servicio
    query = db.query(Order).join(Lead).filter(Order.product_type == ProductType.SERVICE)
    
    # Filtro por estado
    if status_filter:
        try:
            status_enum = OrderStatus[status_filter.upper()]
            query = query.filter(Order.status == status_enum)
        except KeyError:
            pass
    
    # Búsqueda
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Lead.nombre_negocio.ilike(search_pattern),
                Lead.nombre.ilike(search_pattern),
                Lead.email.ilike(search_pattern)
            )
        )
    
    # Ordenar por fecha de creación ascendente (más antigua primero) para priorizar
    orders = query.order_by(Order.created_at.asc()).all()
    
    # Mapear a response
    result = []
    for order in orders:
        lead = order.lead
        result.append(OrderListItem(
            id=order.id,
            lead_id=lead.id,
            client_name=lead.nombre,
            client_email=lead.email,
            client_phone=lead.telefono,
            client_whatsapp=lead.whatsapp,
            business_name=lead.nombre_negocio,
            amount=order.amount,
            status=order.status.value,
            score_inicial=lead.score_visibilidad,
            created_at=order.created_at,
            completed_at=order.completed_at,
            pais=lead.pais,  # Incluir país
            idioma=lead.idioma  # Incluir idioma
        ))
    
    return result


@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(order_id: int, db: Session = Depends(get_db)):
    """
    Obtiene detalle completo de una orden
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada"
        )
    
    lead = order.lead
    
    # Generar checklist basado en fallos críticos
    checklist = _generate_checklist(lead.fallos_criticos, lead.audit_data)
    
    return OrderDetailResponse(
        id=order.id,
        lead_id=lead.id,
        client_name=lead.nombre,
        client_email=lead.email,
        client_phone=lead.telefono,
        client_whatsapp=lead.whatsapp,
        business_name=lead.nombre_negocio,
        amount=order.amount,
        status=order.status.value,
        created_at=order.created_at,
        completed_at=order.completed_at,
        notes=order.notes,
        score_inicial=lead.score_visibilidad,
        fallos_criticos=lead.fallos_criticos,
        audit_data=lead.audit_data,
        checklist=checklist
    )


@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    request: UpdateOrderStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de una orden
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada"
        )
    
    # Validar estado
    try:
        new_status = OrderStatus[request.status.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido. Use: PENDING, IN_PROGRESS, COMPLETED"
        )
    
    order.status = new_status
    db.commit()
    
    return {"message": "Estado actualizado", "order_id": order_id, "new_status": new_status.value}


@router.post("/orders/{order_id}/complete")
async def complete_order(
    order_id: int,
    request: CompleteOrderRequest,
    db: Session = Depends(get_db)
):
    """
    Marca una orden como completada y envía email al cliente
    """
    from email_service import email_service
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada"
        )
    
    lead = order.lead
    
    # Actualizar orden
    order.status = OrderStatus.COMPLETED
    order.completed_at = datetime.utcnow()
    if request.notes:
        order.notes = request.notes
    
    db.commit()
    
    # Enviar email de notificación
    try:
        # Determinar idioma según país
        language_map = {
            'BR': 'pt',
            'ES': 'es',
            'MX': 'es',
            'AR': 'es',
            'CL': 'es',
            'CO': 'es',
            'PE': 'es',
            'VE': 'es',
            'UY': 'es',
            'PY': 'es',
            'EC': 'es',
            'BO': 'es',
        }
        language = language_map.get(lead.pais, 'en')
        
        # Generar resumen de cambios
        changes_summary = """
        ✅ Negocio reclamado y verificado en Google My Business
        📸 Fotos profesionales subidas con geotags GPS
        📝 Descripción optimizada con keywords relevantes
        🏷️ Categorías actualizadas correctamente
        🕐 Horarios de atención configurados
        📍 NAP (Nombre, Dirección, Teléfono) verificado
        ⚡ Atributos y servicios configurados
        """
        
        # Calcular score después (estimación: score inicial + 15-20 puntos)
        score_before = lead.score_visibilidad or 50
        score_after = min(100, score_before + 18)
        
        email_sent = email_service.send_completion_email(
            to_email=lead.email,
            client_name=lead.nombre,
            business_name=lead.nombre_negocio,
            score_before=score_before,
            score_after=score_after,
            changes_summary=changes_summary,
            report_url=request.notes if request.notes and request.notes.startswith('http') else None,
            language=language
        )
        
        return {
            "message": "Orden completada exitosamente",
            "email_sent": email_sent,
            "order_id": order_id
        }
    except Exception as e:
        print(f"Error enviando email: {e}")
        return {
            "message": "Orden completada pero hubo un error al enviar el email",
            "email_sent": False,
            "error": str(e),
            "order_id": order_id
        }


# Helper Functions
def _generate_checklist(fallos_criticos: Optional[dict], audit_data: Optional[dict]) -> List[ChecklistItem]:
    """
    Genera un checklist basado en los fallos críticos detectados
    """
    checklist = []
    
    # Checklist base para servicio completo
    base_tasks = [
        {"id": "reclamar_perfil", "text": "🏢 Reclamar perfil de Google Business"},
        {"id": "optimizar_descripcion", "text": "📝 Optimizar descripción con keywords locales"},
        {"id": "subir_fotos", "text": "📸 Subir 5 fotos profesionales con geoetiquetado"},
        {"id": "configurar_mensajes", "text": "💬 Configurar mensajes automáticos de respuesta"},
        {"id": "horarios", "text": "⏰ Verificar y actualizar horarios de atención"},
        {"id": "crear_landing", "text": "🌐 Crear/optimizar landing page SEO"},
        {"id": "estrategia_resenas", "text": "⭐ Implementar estrategia de reseñas (90 días)"},
        {"id": "seguimiento_mes1", "text": "📊 Seguimiento mes 1: Revisar métricas"},
        {"id": "seguimiento_mes2", "text": "📊 Seguimiento mes 2: Ajustar estrategia"},
        {"id": "seguimiento_mes3", "text": "📊 Seguimiento mes 3: Reporte final"}
    ]
    
    # Agregar tareas específicas basadas en fallos críticos
    if fallos_criticos:
        if isinstance(fallos_criticos, list):
            for i, fallo in enumerate(fallos_criticos):
                if isinstance(fallo, dict):
                    titulo = fallo.get('titulo', fallo.get('title', ''))
                    if 'no reclamado' in titulo.lower():
                        # Ya está en base_tasks
                        pass
                    elif 'sitio web' in titulo.lower():
                        # Ya está en base_tasks (crear_landing)
                        pass
                    elif 'fotos' in titulo.lower():
                        # Ya está en base_tasks
                        pass
    
    # Convertir a ChecklistItem
    for task in base_tasks:
        checklist.append(ChecklistItem(
            id=task["id"],
            text=task["text"],
            completed=False
        ))
    
    return checklist


async def _send_completion_email(client_email: str, client_name: str, business_name: str) -> bool:
    """
    Envía email de completado al cliente
    
    TODO: Integrar con servicio real de email (SendGrid, Mailgun, etc.)
    Por ahora solo retorna True simulando envío exitoso
    """
    # Plantilla del email
    email_content = f"""
    Hola {client_name},
    
    ¡Excelentes noticias! 🎉
    
    Tu negocio '{business_name}' ya está completamente optimizado para búsquedas locales.
    
    ✅ Hemos completado:
    - Reclamación y optimización de tu perfil de Google Business
    - Creación de landing page SEO optimizada
    - Actualización de fotos profesionales con geoetiquetado
    - Configuración de mensajes automáticos
    - Implementación de estrategia de reseñas
    
    📊 En los próximos días verás:
    - Mayor visibilidad en búsquedas locales de Google Maps
    - Incremento en llamadas y visitas al negocio
    - Mejora en el posicionamiento vs. competencia
    
    Recuerda que incluimos 3 meses de seguimiento. Te contactaremos mensualmente
    para revisar métricas y ajustar la estrategia.
    
    ¿Tienes preguntas? Responde este email o contáctanos por WhatsApp.
    
    ¡Éxito con tu negocio!
    
    Equipo Lokigi
    🚀 Crecimiento Local Garantizado
    """
    
    # TODO: Implementar envío real
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail
    # message = Mail(
    #     from_email='noreply@lokigi.com',
    #     to_emails=client_email,
    #     subject=f'¡Tu negocio {business_name} ya está optimizado! 🎉',
    #     html_content=email_content
    # )
    # sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    # response = sg.send(message)
    
    print(f"📧 Email enviado a {client_email}")
    print(email_content)
    
    return True


# ========================================
# Endpoints de Gestión de Tareas
# ========================================

@router.get("/orders/{order_id}/tasks", response_model=TaskListResponse)
def get_order_tasks(
    order_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las tareas de una orden con estadísticas.
    
    Devuelve:
    - Lista completa de tareas ordenadas por priority desc
    - Porcentaje de completitud
    - Número de tareas pendientes
    """
    # Verificar que la orden existe
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden {order_id} no encontrada"
        )
    
    # Obtener tareas ordenadas por prioridad
    tasks = db.query(Task).filter(
        Task.order_id == order_id
    ).order_by(
        Task.priority.desc(),
        Task.order_index.asc()
    ).all()
    
    # Calcular estadísticas
    completion_percentage = get_task_completion_percentage(order_id, db)
    pending_tasks = sum(1 for task in tasks if not task.is_completed)
    
    return TaskListResponse(
        tasks=[TaskResponse.from_orm(task) for task in tasks],
        completion_percentage=completion_percentage,
        pending_tasks=pending_tasks
    )


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    request: UpdateTaskRequest,
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de una tarea.
    
    Permite al trabajador:
    - Marcar una tarea como completada o incompleta
    - Agregar notas sobre el trabajo realizado
    
    Args:
        task_id: ID de la tarea
        request: Datos de actualización (is_completed, notes)
    
    Returns:
        Tarea actualizada
    """
    # Buscar la tarea
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea {task_id} no encontrada"
        )
    
    # Actualizar según el estado solicitado
    if request.is_completed:
        mark_task_completed(task_id, request.notes or "", db)
    else:
        mark_task_incomplete(task_id, db)
    
    # Refrescar para obtener cambios
    db.refresh(task)
    
    return TaskResponse.from_orm(task)


@router.post("/orders/{order_id}/complete")
def complete_order(
    order_id: int,
    request: CompleteOrderRequest,
    db: Session = Depends(get_db)
):
    """
    Marca una orden como completada y dispara notificaciones.
    
    Acciones:
    1. Cambia el status de la orden a COMPLETED
    2. Establece la fecha de completitud
    3. Guarda notas finales (opcional)
    4. Envía email al cliente notificando la finalización
    
    Args:
        order_id: ID de la orden
        request: Notas finales opcionales
    
    Returns:
        Confirmación de completitud
    """
    # Buscar la orden
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden {order_id} no encontrada"
        )
    
    # Verificar que no esté ya completada
    if order.status == OrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La orden ya está completada"
        )
    
    # Actualizar estado
    order.status = OrderStatus.COMPLETED
    order.completed_at = datetime.utcnow()
    
    # Agregar notas si se proporcionaron
    if request.notes:
        if order.notes:
            order.notes += f"\n\n[COMPLETITUD] {request.notes}"
        else:
            order.notes = f"[COMPLETITUD] {request.notes}"
    
    db.commit()
    db.refresh(order)
    
    # Obtener lead para datos del cliente
    lead = db.query(Lead).filter(Lead.id == order.lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {order.lead_id} no encontrado"
        )
    
    # Enviar email de notificación
    _send_completion_email(
        client_email=lead.email,
        client_name=lead.nombre,
        business_name=lead.nombre_negocio,
        score_inicial=lead.score_inicial or 0,
        score_final=85  # TODO: Calcular score final real
    )
    
    return {
        "success": True,
        "message": f"Orden {order_id} completada exitosamente",
        "order_id": order.id,
        "completed_at": order.completed_at,
        "status": order.status.value
    }


# ==========================================
# ANALYTICS ENDPOINTS
# ==========================================

class LeadsByCountryResponse(BaseModel):
    """Leads agrupados por país"""
    country: str
    count: int
    revenue: float
    percentage: float


class AnalyticsResponse(BaseModel):
    """Respuesta de analytics"""
    total_leads: int
    total_orders: int
    total_revenue: float
    conversion_rate: float
    leads_by_country: List[LeadsByCountryResponse]


# ==========================================
# ADVANCED BUSINESS INTELLIGENCE ENDPOINTS
# ==========================================

class ConversionMetrics(BaseModel):
    """Métricas de conversión por tipo de producto"""
    total_leads: int
    diagnoses_given: int
    ebook_purchases: int
    service_purchases: int
    subscriptions: int
    diagnosis_to_ebook_rate: float
    diagnosis_to_service_rate: float
    diagnosis_to_subscription_rate: float
    overall_conversion_rate: float


class RegionPerformance(BaseModel):
    """Desempeño por región"""
    country: str
    country_name: str
    flag: str
    total_leads: int
    total_orders: int
    total_revenue: float
    conversion_rate: float
    avg_order_value: float
    roi_score: float  # Métrica combinada: revenue / leads * conversion_rate


class SubscriptionLTV(BaseModel):
    """Lifetime Value de suscripciones"""
    active_subscriptions: int
    canceled_subscriptions: int
    avg_subscription_days: float
    avg_lifetime_months: float
    estimated_ltv: float  # $29 * avg_months
    churn_rate: float


class OperationalEfficiency(BaseModel):
    """Eficiencia operativa del equipo"""
    total_service_orders: int
    completed_orders: int
    pending_orders: int
    in_progress_orders: int
    avg_completion_time_hours: float
    avg_completion_time_days: float
    fastest_completion_hours: float
    slowest_completion_hours: float
    completion_rate: float


class AdvancedAnalyticsResponse(BaseModel):
    """Respuesta completa de Business Intelligence"""
    time_range: str
    conversion_metrics: ConversionMetrics
    region_performance: List[RegionPerformance]
    subscription_ltv: SubscriptionLTV
    operational_efficiency: OperationalEfficiency


@router.get("/analytics/business-intelligence", response_model=AdvancedAnalyticsResponse)
async def get_business_intelligence(
    time_range: str = "30d",
    db: Session = Depends(get_db)
):
    """
    Business Intelligence Dashboard - KPIs avanzados para analistas de datos
    
    Métricas:
    1. Conversión: % de leads que avanzan del diagnóstico a compras
    2. Desempeño Regional: ROI por país
    3. LTV: Cuánto tiempo se quedan los suscriptores
    4. Eficiencia: Tiempo promedio de cierre de órdenes
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func, case
    
    # Calcular fecha de inicio
    if time_range == "7d":
        start_date = datetime.now() - timedelta(days=7)
    elif time_range == "30d":
        start_date = datetime.now() - timedelta(days=30)
    elif time_range == "90d":
        start_date = datetime.now() - timedelta(days=90)
    else:  # "all"
        start_date = datetime.min
    
    # ========== 1. MÉTRICAS DE CONVERSIÓN ==========
    
    # Total leads en el período
    total_leads = db.query(Lead).filter(Lead.created_at >= start_date).count()
    
    # Leads que recibieron diagnóstico (tienen score)
    diagnoses_given = db.query(Lead).filter(
        Lead.created_at >= start_date,
        Lead.score_visibilidad.isnot(None)
    ).count()
    
    # Órdenes por tipo de producto
    ebook_purchases = db.query(Order).join(Lead).filter(
        Order.created_at >= start_date,
        Order.product_type == ProductType.EBOOK
    ).count()
    
    service_purchases = db.query(Order).join(Lead).filter(
        Order.created_at >= start_date,
        Order.product_type == ProductType.SERVICE
    ).count()
    
    # Suscripciones activas creadas en el período
    subscriptions = db.query(Lead).filter(
        Lead.created_at >= start_date,
        Lead.premium_subscriber == True
    ).count()
    
    # Calcular tasas de conversión
    diagnosis_to_ebook = (ebook_purchases / diagnoses_given * 100) if diagnoses_given > 0 else 0
    diagnosis_to_service = (service_purchases / diagnoses_given * 100) if diagnoses_given > 0 else 0
    diagnosis_to_subscription = (subscriptions / diagnoses_given * 100) if diagnoses_given > 0 else 0
    
    total_purchases = ebook_purchases + service_purchases + subscriptions
    overall_conversion = (total_purchases / diagnoses_given * 100) if diagnoses_given > 0 else 0
    
    conversion_metrics = ConversionMetrics(
        total_leads=total_leads,
        diagnoses_given=diagnoses_given,
        ebook_purchases=ebook_purchases,
        service_purchases=service_purchases,
        subscriptions=subscriptions,
        diagnosis_to_ebook_rate=round(diagnosis_to_ebook, 2),
        diagnosis_to_service_rate=round(diagnosis_to_service, 2),
        diagnosis_to_subscription_rate=round(diagnosis_to_subscription, 2),
        overall_conversion_rate=round(overall_conversion, 2)
    )
    
    # ========== 2. DESEMPEÑO POR REGIÓN ==========
    
    # Mapeo de países
    country_names = {
        'BR': 'Brasil',
        'AR': 'Argentina',
        'MX': 'México',
        'US': 'Estados Unidos',
        'CO': 'Colombia',
        'CL': 'Chile',
        'PE': 'Perú',
        'ES': 'España',
    }
    
    country_flags = {
        'BR': '🇧🇷', 'AR': '🇦🇷', 'MX': '🇲🇽', 'US': '🇺🇸',
        'CO': '🇨🇴', 'CL': '🇨🇱', 'PE': '🇵🇪', 'ES': '🇪🇸',
    }
    
    # Query por país
    countries = db.query(Lead.pais).filter(Lead.created_at >= start_date).distinct().all()
    region_performance_list = []
    
    for (country_code,) in countries:
        if not country_code:
            continue
        
        # Leads del país
        country_leads = db.query(Lead).filter(
            Lead.created_at >= start_date,
            Lead.pais == country_code
        ).count()
        
        # Órdenes del país
        country_orders = db.query(Order).join(Lead).filter(
            Order.created_at >= start_date,
            Lead.pais == country_code
        ).count()
        
        # Revenue del país
        country_revenue = db.query(func.sum(Order.amount)).join(Lead).filter(
            Order.created_at >= start_date,
            Lead.pais == country_code,
            Order.status == OrderStatus.COMPLETED
        ).scalar() or 0.0
        
        # Métricas calculadas
        conversion = (country_orders / country_leads * 100) if country_leads > 0 else 0
        avg_order = (country_revenue / country_orders) if country_orders > 0 else 0
        
        # ROI Score: revenue normalizado por lead * conversion rate
        roi_score = (country_revenue / country_leads * conversion) if country_leads > 0 else 0
        
        region_performance_list.append(RegionPerformance(
            country=country_code,
            country_name=country_names.get(country_code, country_code),
            flag=country_flags.get(country_code, '🌍'),
            total_leads=country_leads,
            total_orders=country_orders,
            total_revenue=round(country_revenue, 2),
            conversion_rate=round(conversion, 2),
            avg_order_value=round(avg_order, 2),
            roi_score=round(roi_score, 2)
        ))
    
    # Ordenar por ROI score descendente
    region_performance_list.sort(key=lambda x: x.roi_score, reverse=True)
    
    # ========== 3. SUBSCRIPTION LTV ==========
    
    # Suscripciones activas
    active_subs = db.query(Lead).filter(
        Lead.premium_subscriber == True,
        Lead.subscription_status == 'active'
    ).count()
    
    # Suscripciones canceladas
    canceled_subs = db.query(Lead).filter(
        Lead.premium_subscriber == False,
        Lead.subscription_id.isnot(None)  # Tuvieron suscripción
    ).count()
    
    # Calcular duración promedio de suscripciones canceladas
    canceled_subscriptions = db.query(Lead).filter(
        Lead.premium_subscriber == False,
        Lead.subscription_id.isnot(None),
        Lead.subscription_current_period_end.isnot(None)
    ).all()
    
    total_days = 0
    count_with_dates = 0
    
    for sub in canceled_subscriptions:
        if sub.created_at and sub.subscription_current_period_end:
            days = (sub.subscription_current_period_end - sub.created_at).days
            if days > 0:
                total_days += days
                count_with_dates += 1
    
    avg_days = (total_days / count_with_dates) if count_with_dates > 0 else 30.0  # Default 1 mes
    avg_months = avg_days / 30.0
    estimated_ltv = avg_months * 29.0  # $29/mes
    
    # Churn rate
    total_subs = active_subs + canceled_subs
    churn = (canceled_subs / total_subs * 100) if total_subs > 0 else 0
    
    subscription_ltv = SubscriptionLTV(
        active_subscriptions=active_subs,
        canceled_subscriptions=canceled_subs,
        avg_subscription_days=round(avg_days, 1),
        avg_lifetime_months=round(avg_months, 2),
        estimated_ltv=round(estimated_ltv, 2),
        churn_rate=round(churn, 2)
    )
    
    # ========== 4. EFICIENCIA OPERATIVA ==========
    
    # Órdenes de servicio ($99)
    service_orders = db.query(Order).filter(
        Order.created_at >= start_date,
        Order.product_type == ProductType.SERVICE
    ).all()
    
    total_service = len(service_orders)
    completed = len([o for o in service_orders if o.status == OrderStatus.COMPLETED])
    pending = len([o for o in service_orders if o.status == OrderStatus.PENDING])
    in_progress = len([o for o in service_orders if o.status == OrderStatus.IN_PROGRESS])
    
    # Calcular tiempos de completitud
    completion_times = []
    for order in service_orders:
        if order.status == OrderStatus.COMPLETED and order.completed_at:
            time_diff = (order.completed_at - order.created_at).total_seconds() / 3600  # horas
            completion_times.append(time_diff)
    
    avg_hours = sum(completion_times) / len(completion_times) if completion_times else 0
    fastest = min(completion_times) if completion_times else 0
    slowest = max(completion_times) if completion_times else 0
    completion_rate = (completed / total_service * 100) if total_service > 0 else 0
    
    operational_efficiency = OperationalEfficiency(
        total_service_orders=total_service,
        completed_orders=completed,
        pending_orders=pending,
        in_progress_orders=in_progress,
        avg_completion_time_hours=round(avg_hours, 2),
        avg_completion_time_days=round(avg_hours / 24, 2),
        fastest_completion_hours=round(fastest, 2),
        slowest_completion_hours=round(slowest, 2),
        completion_rate=round(completion_rate, 2)
    )
    
    return AdvancedAnalyticsResponse(
        time_range=time_range,
        conversion_metrics=conversion_metrics,
        region_performance=region_performance_list,
        subscription_ltv=subscription_ltv,
        operational_efficiency=operational_efficiency
    )


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    time_range: str = "30d",
    db: Session = Depends(get_db)
):
    """
    Obtiene analytics para dashboard de admin
    
    Decisión crítica: ¿Dónde invertir tiempo (único capital)?
    
    Parámetros:
    - time_range: "7d", "30d", "all"
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Calcular fecha de inicio según time_range
    if time_range == "7d":
        start_date = datetime.now() - timedelta(days=7)
    elif time_range == "30d":
        start_date = datetime.now() - timedelta(days=30)
    else:  # "all"
        start_date = datetime.min
    
    # Query base con filtro de fecha
    leads_query = db.query(Lead).filter(Lead.created_at >= start_date)
    orders_query = db.query(Order).filter(Order.created_at >= start_date)
    
    # Total leads
    total_leads = leads_query.count()
    
    # Total orders (solo COMPLETED porque son pagados)
    total_orders = orders_query.filter(Order.status == OrderStatus.COMPLETED).count()
    
    # Total revenue
    total_revenue = db.query(func.sum(Order.amount)).filter(
        Order.created_at >= start_date,
        Order.status == OrderStatus.COMPLETED
    ).scalar() or 0.0
    
    # Conversion rate
    conversion_rate = (total_orders / total_leads * 100) if total_leads > 0 else 0.0
    
    # Leads por país (agrupado)
    leads_by_country = db.query(
        Lead.pais.label('country'),
        func.count(Lead.id).label('count')
    ).filter(
        Lead.created_at >= start_date
    ).group_by(Lead.pais).all()
    
    # Revenue por país
    revenue_by_country = {}
    for country_code in [row.country for row in leads_by_country]:
        country_revenue = db.query(func.sum(Order.amount)).join(Lead).filter(
            Lead.pais == country_code,
            Order.created_at >= start_date,
            Order.status == OrderStatus.COMPLETED
        ).scalar() or 0.0
        revenue_by_country[country_code] = country_revenue
    
    # Construir response
    leads_by_country_response = []
    for row in leads_by_country:
        country = row.country or 'OTHER'
        count = row.count
        revenue = revenue_by_country.get(country, 0.0)
        percentage = (count / total_leads * 100) if total_leads > 0 else 0.0
        
        leads_by_country_response.append(LeadsByCountryResponse(
            country=country,
            count=count,
            revenue=revenue,
            percentage=percentage
        ))
    
    # Ordenar por revenue descendente
    leads_by_country_response.sort(key=lambda x: x.revenue, reverse=True)
    
    return AnalyticsResponse(
        total_leads=total_leads,
        total_orders=total_orders,
        total_revenue=total_revenue,
        conversion_rate=conversion_rate,
        leads_by_country=leads_by_country_response
    )


# ==========================================
# ENDPOINT PARA GUARDAR NOTAS
# ==========================================

class SaveNotesRequest(BaseModel):
    """Request para guardar notas internas"""
    notes: str


@router.post("/orders/{order_id}/notes")
async def save_order_notes(
    order_id: int,
    request: SaveNotesRequest,
    db: Session = Depends(get_db)
):
    """
    Guarda notas internas de una orden
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden {order_id} no encontrada"
        )
    
    order.notes = request.notes
    db.commit()
    
    return {"message": "Notas guardadas correctamente"}


# ==========================================
# ENDPOINT PARA AI COPYWRITER
# ==========================================

class GenerateCopyRequest(BaseModel):
    """Request para generar contenido con AI"""
    business_name: str
    business_category: Optional[str] = None


class GenerateCopyResponse(BaseModel):
    """Response con contenido generado por AI"""
    description: str
    review_responses: List[str]


@router.post("/orders/{order_id}/generate-copy", response_model=GenerateCopyResponse)
async def generate_copy_with_ai(
    order_id: int,
    request: GenerateCopyRequest,
    db: Session = Depends(get_db)
):
    """
    Genera descripción de negocio y respuestas a reseñas usando Gemini AI
    """
    from gemini_service import GeminiAIService
    from i18n_service import Language
    
    # Verificar que la orden existe
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden {order_id} no encontrada"
        )
    
    lead = order.lead
    
    # Determinar idioma según país
    language_map = {
        'BR': Language.PORTUGUESE,
        'ES': Language.SPANISH,
        'MX': Language.SPANISH,
        'AR': Language.SPANISH,
        'CL': Language.SPANISH,
        'CO': Language.SPANISH,
        'PE': Language.SPANISH,
        'VE': Language.SPANISH,
        'UY': Language.SPANISH,
        'PY': Language.SPANISH,
        'EC': Language.SPANISH,
        'BO': Language.SPANISH,
    }
    language = language_map.get(lead.pais, Language.ENGLISH)
    
    # Inicializar servicio Gemini
    gemini_service = GeminiAIService(language)
    
    if not gemini_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de IA no disponible. Verifica GEMINI_API_KEY."
        )
    
    try:
        # Generar descripción del negocio (150 palabras)
        description_prompt = f"""Generate a professional and engaging business description for Google My Business.

Business Name: {request.business_name}
Category: {request.business_category or 'General business'}
Target: Local customers looking for this type of service

Requirements:
- Exactly 150 words
- Highlight unique value proposition
- Include keywords naturally
- Professional tone
- Call to action at the end
- Write in {language.value} language

Description:"""
        
        description_response = gemini_service.model.generate_content(description_prompt)
        description = description_response.text.strip()
        
        # Generar 3 respuestas a reseñas negativas
        review_responses = []
        for i in range(3):
            tone = ["empathetic and professional", "solution-focused", "appreciative and constructive"][i]
            review_prompt = f"""Generate a response to a negative customer review for {request.business_name}.

Tone: {tone}
Requirements:
- Acknowledge the issue
- Apologize sincerely
- Offer a solution
- Invite them back
- 50-80 words
- Write in {language.value} language

Response:"""
            
            review_response = gemini_service.model.generate_content(review_prompt)
            review_responses.append(review_response.text.strip())
        
        return GenerateCopyResponse(
            description=description,
            review_responses=review_responses
        )
        
    except Exception as e:
        print(f"Error generando contenido con Gemini: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar contenido: {str(e)}"
        )


# ==========================================
# ENDPOINT PARA GEOTAGGING DE FOTOS
# ==========================================

class GeotagResponse(BaseModel):
    """Response del servicio de geotagging"""
    latitude: float
    longitude: float
    address: str
    files_processed: int
    download_url: str


@router.post("/orders/{order_id}/geotag-photos", response_model=GeotagResponse)
async def geotag_photos(
    order_id: int,
    business_name: str = Form(...),
    business_address: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Geotag fotos con coordenadas GPS del negocio
    """
    from PIL import Image
    import piexif
    import requests
    
    # Verificar que la orden existe
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden {order_id} no encontrada"
        )
    
    lead = order.lead
    
    # 1. Obtener coordenadas GPS
    # Usar dirección del negocio o construir una query
    search_query = business_address if business_address else f"{business_name}"
    
    # Usar Nominatim (OpenStreetMap) - GRATIS
    try:
        geocoding_url = f"https://nominatim.openstreetmap.org/search?q={search_query}&format=json&limit=1"
        headers = {'User-Agent': 'Lokigi-SEO-Tool/1.0'}
        response = requests.get(geocoding_url, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se pudieron obtener coordenadas para esta dirección"
            )
        
        latitude = float(results[0]['lat'])
        longitude = float(results[0]['lon'])
        display_name = results[0]['display_name']
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener coordenadas: {str(e)}"
        )
    
    # 2. Procesar fotos y añadir EXIF GPS
    processed_files = []
    
    try:
        for upload_file in files:
            # Leer imagen
            contents = await upload_file.read()
            image = Image.open(io.BytesIO(contents))
            
            # Convertir a formato GPS EXIF
            def to_deg(value, loc):
                """Convierte decimal a grados/minutos/segundos para EXIF"""
                if value < 0:
                    loc_value = loc[0]
                elif value > 0:
                    loc_value = loc[1]
                else:
                    loc_value = ""
                
                abs_value = abs(value)
                deg = int(abs_value)
                t1 = (abs_value - deg) * 60
                min = int(t1)
                sec = round((t1 - min) * 60, 5)
                
                return (deg, 1), (min, 1), (int(sec * 100), 100), loc_value
            
            lat = to_deg(latitude, ["S", "N"])
            lng = to_deg(longitude, ["W", "E"])
            
            # Crear datos EXIF GPS
            exif_dict = piexif.load(image.info.get("exif", b""))
            
            gps_ifd = {
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSAltitudeRef: 0,
                piexif.GPSIFD.GPSAltitude: (0, 1),
                piexif.GPSIFD.GPSLatitudeRef: lat[3],
                piexif.GPSIFD.GPSLatitude: ((lat[0][0], lat[0][1]), (lat[1][0], lat[1][1]), (lat[2][0], lat[2][1])),
                piexif.GPSIFD.GPSLongitudeRef: lng[3],
                piexif.GPSIFD.GPSLongitude: ((lng[0][0], lng[0][1]), (lng[1][0], lng[1][1]), (lng[2][0], lng[2][1])),
            }
            
            exif_dict["GPS"] = gps_ifd
            exif_bytes = piexif.dump(exif_dict)
            
            # Guardar imagen con EXIF
            output = io.BytesIO()
            image.save(output, format='JPEG', exif=exif_bytes)
            output.seek(0)
            
            processed_files.append((upload_file.filename, output.getvalue()))
        
        # 3. Crear ZIP con las fotos procesadas
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, file_data in processed_files:
                zip_file.writestr(f"geotagged_{filename}", file_data)
        
        zip_buffer.seek(0)
        
        # 4. Guardar ZIP temporalmente
        temp_dir = tempfile.gettempdir()
        zip_filename = f"geotagged_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        with open(zip_path, 'wb') as f:
            f.write(zip_buffer.getvalue())
        
        # 5. Construir URL de descarga
        download_url = f"/api/dashboard/download/{zip_filename}"
        
        return GeotagResponse(
            latitude=latitude,
            longitude=longitude,
            address=display_name,
            files_processed=len(processed_files),
            download_url=download_url
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar fotos: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Descarga archivo temporal (ZIP de fotos geoetiquetadas)
    """
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/zip'
    )


# ==========================================
# ENDPOINT PARA CHECKLIST DE FINALIZACIÓN
# ==========================================

class ChecklistState(BaseModel):
    """Estado del checklist de finalización"""
    items: Dict[str, bool]


@router.get("/orders/{order_id}/checklist", response_model=ChecklistState)
async def get_checklist(order_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el estado del checklist de finalización
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden {order_id} no encontrada"
        )
    
    # Parsear checklist desde order.notes (formato JSON)
    try:
        import json
        if order.notes:
            notes_data = json.loads(order.notes)
            if isinstance(notes_data, dict) and 'checklist' in notes_data:
                return ChecklistState(items=notes_data['checklist'])
    except:
        pass
    
    # Devolver checklist vacío por defecto
    return ChecklistState(items={})


@router.post("/orders/{order_id}/checklist")
async def save_checklist(
    order_id: int,
    checklist: ChecklistState,
    db: Session = Depends(get_db)
):
    """
    Guarda el estado del checklist de finalización
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden {order_id} no encontrada"
        )
    
    # Guardar checklist en order.notes como JSON
    import json
    try:
        # Preservar otras notas si existen
        notes_data = {}
        if order.notes:
            try:
                notes_data = json.loads(order.notes)
            except:
                # Si notes no es JSON, guardarlo como texto plano
                notes_data = {'text': order.notes}
        
        notes_data['checklist'] = checklist.items
        order.notes = json.dumps(notes_data)
        db.commit()
        
        return {"success": True, "message": "Checklist guardado correctamente"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar checklist: {str(e)}"
        )
