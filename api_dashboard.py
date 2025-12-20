"""
Dashboard API - Endpoints para el panel operativo del equipo
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

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
    
    # Ordenar por fecha de creación descendente
    orders = query.order_by(Order.created_at.desc()).all()
    
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
            completed_at=order.completed_at
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
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada"
        )
    
    # Actualizar orden
    order.status = OrderStatus.COMPLETED
    order.completed_at = datetime.utcnow()
    if request.notes:
        order.notes = request.notes
    
    db.commit()
    
    # Enviar email al cliente
    lead = order.lead
    email_sent = await _send_completion_email(
        client_email=lead.email,
        client_name=lead.nombre,
        business_name=lead.nombre_negocio
    )
    
    return {
        "message": "Orden completada exitosamente",
        "order_id": order_id,
        "email_sent": email_sent
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
