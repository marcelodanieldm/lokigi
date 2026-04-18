"""
Business Logic - Generador automático de tareas
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models import Task, Order, Lead, TaskCategory


def generate_tasks_from_audit(
    order_id: int,
    audit_data: Optional[Dict[str, Any]],
    fallos_criticos: Optional[Any],
    db: Session
) -> List[Task]:
    """
    Genera tareas automáticamente basándose en los datos de auditoría
    
    Args:
        order_id: ID de la orden
        audit_data: Datos completos de la auditoría
        fallos_criticos: Lista de fallos críticos detectados
        db: Sesión de base de datos
        
    Returns:
        Lista de tareas creadas
    """
    tasks = []
    order_index = 1
    
    # Obtener la orden y el lead
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return tasks
    
    lead = order.lead
    
    # Analizar fallos críticos
    if fallos_criticos:
        fallos_list = fallos_criticos if isinstance(fallos_criticos, list) else []
        
        for fallo in fallos_list:
            if not isinstance(fallo, dict):
                continue
                
            titulo = fallo.get('titulo', fallo.get('title', '')).lower()
            
            # CASO 1: Perfil no reclamado
            if 'no reclamado' in titulo or 'sin reclamar' in titulo or 'no verificado' in titulo:
                tasks.append(Task(
                    order_id=order_id,
                    description=f"🏢 Reclamar y verificar la propiedad del negocio '{lead.nombre_negocio}' en Google Business Profile",
                    category=TaskCategory.SEO,
                    priority=10,  # Máxima prioridad
                    order_index=order_index,
                    notes="CRÍTICO: Sin esto, el cliente no tiene control sobre su perfil. Riesgo de información incorrecta."
                ))
                order_index += 1
                
            # CASO 2: Sin sitio web
            if 'sitio web' in titulo or 'website' in titulo or 'página web' in titulo:
                tasks.append(Task(
                    order_id=order_id,
                    description=f"🌐 Crear landing page SEO optimizada para '{lead.nombre_negocio}' con keywords locales",
                    category=TaskCategory.CONTENIDO,
                    priority=8,
                    order_index=order_index,
                    notes="La página debe incluir: dirección, horarios, servicios, formulario de contacto y CTAs claros."
                ))
                order_index += 1
                
            # CASO 3: Fotos desactualizadas o sin fotos
            if 'fotos' in titulo or 'imágenes' in titulo or 'photos' in titulo:
                tasks.append(Task(
                    order_id=order_id,
                    description="📸 Subir 5 fotos de alta calidad con etiquetas EXIF de geolocalización",
                    category=TaskCategory.CONTENIDO,
                    priority=7,
                    order_index=order_index,
                    notes="Las fotos deben ser: fachada, interior, productos/servicios, equipo, logo. Todas con geotags."
                ))
                order_index += 1
    
    # Tareas basadas en métricas del audit_data
    if audit_data:
        # CASO 4: Rating bajo (< 4.0)
        rating = None
        if isinstance(audit_data, dict):
            rating = audit_data.get('rating')
            if rating is None:
                # Buscar en nested structures
                datos = audit_data.get('datos_analizados', {})
                rating = datos.get('rating')
        
        if rating and rating < 4.0:
            tasks.append(Task(
                order_id=order_id,
                description="⭐ Configurar sistema de respuesta rápida a reseñas negativas (< 24 horas)",
                category=TaskCategory.SEO,
                priority=9,
                order_index=order_index,
                notes=f"Rating actual: {rating}/5.0. Implementar templates de respuesta profesional y protocolo de seguimiento."
            ))
            order_index += 1
            
        # CASO 5: Pocas reseñas
        num_resenas = None
        if isinstance(audit_data, dict):
            num_resenas = audit_data.get('numero_resenas')
            if num_resenas is None:
                datos = audit_data.get('datos_analizados', {})
                num_resenas = datos.get('numero_resenas')
        
        if num_resenas and num_resenas < 50:
            tasks.append(Task(
                order_id=order_id,
                description=f"📝 Implementar estrategia de generación de reseñas (Meta: 50+ reseñas en 90 días)",
                category=TaskCategory.SEO,
                priority=6,
                order_index=order_index,
                notes=f"Actualmente: {num_resenas} reseñas. Crear campaña de email post-venta, QR codes en local, incentivos."
            ))
            order_index += 1
    
    # Tareas estándar para todos los pedidos de servicio
    
    # Optimización de descripción
    tasks.append(Task(
        order_id=order_id,
        description="📝 Optimizar descripción del negocio con keywords locales de alto impacto",
        category=TaskCategory.SEO,
        priority=7,
        order_index=order_index,
        notes="Incluir: ciudad, barrio, servicios principales, USP. Máximo 750 caracteres."
    ))
    order_index += 1
    
    # Configuración de mensajería
    tasks.append(Task(
        order_id=order_id,
        description="💬 Configurar mensajes automáticos en Google Business (bienvenida, horarios, FAQ)",
        category=TaskCategory.SEO,
        priority=5,
        order_index=order_index,
        notes="Activar respuestas automáticas para preguntas frecuentes sobre horarios, ubicación y servicios."
    ))
    order_index += 1
    
    # Verificación de horarios
    tasks.append(Task(
        order_id=order_id,
        description="⏰ Verificar y actualizar horarios de atención (incluir horarios especiales)",
        category=TaskCategory.VERIFICACION,
        priority=4,
        order_index=order_index,
        notes="Revisar horarios regulares, días festivos, vacaciones. Configurar alertas para actualizaciones."
    ))
    order_index += 1
    
    # Posts periódicos
    tasks.append(Task(
        order_id=order_id,
        description="📱 Crear calendario de posts para Google Business (4 posts/mes durante 3 meses)",
        category=TaskCategory.CONTENIDO,
        priority=5,
        order_index=order_index,
        notes="Contenido: ofertas, eventos, novedades, tips. Con imágenes y CTAs."
    ))
    order_index += 1
    
    # Seguimiento mes 1
    tasks.append(Task(
        order_id=order_id,
        description="📊 Seguimiento mes 1: Analizar métricas (vistas, clics, llamadas) y ajustar estrategia",
        category=TaskCategory.VERIFICACION,
        priority=3,
        order_index=order_index,
        notes="Revisar Google Insights: impresiones, interacciones, conversiones. Preparar reporte para cliente."
    ))
    order_index += 1
    
    # Seguimiento mes 2
    tasks.append(Task(
        order_id=order_id,
        description="📊 Seguimiento mes 2: Optimización basada en datos del primer mes",
        category=TaskCategory.VERIFICACION,
        priority=2,
        order_index=order_index,
        notes="Ajustar keywords, revisar competencia, optimizar fotos con mejor rendimiento."
    ))
    order_index += 1
    
    # Seguimiento mes 3 y reporte final
    tasks.append(Task(
        order_id=order_id,
        description="📊 Seguimiento mes 3: Reporte final con comparativa antes/después y recomendaciones",
        category=TaskCategory.VERIFICACION,
        priority=1,
        order_index=order_index,
        notes="Preparar informe ejecutivo con: incremento de visibilidad, nuevas llamadas/visitas, ROI estimado."
    ))
    order_index += 1
    
    # Guardar todas las tareas en la base de datos
    for task in tasks:
        db.add(task)
    
    try:
        db.commit()
        # Refrescar para obtener IDs
        for task in tasks:
            db.refresh(task)
    except Exception as e:
        db.rollback()
        raise Exception(f"Error al guardar tareas: {str(e)}")
    
    return tasks


def get_task_completion_percentage(order_id: int, db: Session) -> float:
    """
    Calcula el porcentaje de completado de las tareas de una orden
    
    Args:
        order_id: ID de la orden
        db: Sesión de base de datos
        
    Returns:
        Porcentaje de completado (0-100)
    """
    tasks = db.query(Task).filter(Task.order_id == order_id).all()
    
    if not tasks:
        return 0.0
    
    completed_tasks = sum(1 for task in tasks if task.is_completed)
    return (completed_tasks / len(tasks)) * 100


def get_pending_tasks_count(order_id: int, db: Session) -> int:
    """
    Cuenta las tareas pendientes de una orden
    """
    return db.query(Task).filter(
        Task.order_id == order_id,
        Task.is_completed == False
    ).count()


def get_high_priority_tasks(order_id: int, db: Session) -> List[Task]:
    """
    Obtiene las tareas de alta prioridad (priority >= 7) pendientes
    """
    return db.query(Task).filter(
        Task.order_id == order_id,
        Task.is_completed == False,
        Task.priority >= 7
    ).order_by(Task.priority.desc(), Task.order_index).all()


def mark_task_completed(task_id: int, notes: Optional[str], db: Session) -> Task:
    """
    Marca una tarea como completada
    
    Args:
        task_id: ID de la tarea
        notes: Notas adicionales (opcional)
        db: Sesión de base de datos
        
    Returns:
        Tarea actualizada
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise ValueError(f"Tarea {task_id} no encontrada")
    
    task.is_completed = True
    task.completed_at = datetime.utcnow()
    
    if notes:
        task.notes = notes if not task.notes else f"{task.notes}\n\nActualización: {notes}"
    
    db.commit()
    db.refresh(task)
    
    return task


def mark_task_incomplete(task_id: int, db: Session) -> Task:
    """
    Marca una tarea como no completada (revertir)
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise ValueError(f"Tarea {task_id} no encontrada")
    
    task.is_completed = False
    task.completed_at = None
    
    db.commit()
    db.refresh(task)
    
    return task
