# Dashboard Operativo - Documentación

## 📋 Resumen del Sistema

Sistema completo de gestión operativa para el equipo de trabajo de Lokigi. Permite administrar órdenes de servicio ($99) con un sistema automático de generación de tareas basado en los datos de auditoría.

## 🗄️ Base de Datos

### Modelo `Task` (Nuevo)

```python
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    description = Column(Text, nullable=False)
    category = Column(Enum(TaskCategory), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    
    priority = Column(Integer, nullable=False)  # 1-10 (10 = máxima prioridad)
    order_index = Column(Integer, nullable=False)  # Orden de visualización
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relación inversa
    order = relationship("Order", back_populates="tasks")
```

### Enum `TaskCategory`

```python
class TaskCategory(str, Enum):
    SEO = "SEO"
    CONTENIDO = "CONTENIDO"
    VERIFICACION = "VERIFICACION"
```

### Relación en `Order`

```python
tasks = relationship("Task", back_populates="order", cascade="all, delete-orphan")
```

## 🤖 Generación Automática de Tareas

### Archivo: `task_generator.py`

#### Función Principal: `generate_tasks_from_audit()`

Analiza los datos de auditoría y genera automáticamente de **5 a 12 tareas** por orden.

**Tareas Condicionales** (basadas en fallos críticos):

1. **Perfil no reclamado** 🔴 Prioridad 10
   ```python
   if "no reclamado" in fallos_criticos:
       → "Reclamar y verificar la propiedad del negocio en Google Business Profile"
   ```

2. **Sin sitio web** 🟠 Prioridad 8
   ```python
   if "sitio web" in fallos_criticos:
       → "Crear landing page SEO optimizada con datos del negocio"
   ```

3. **Fotos desactualizadas** 🟡 Prioridad 7
   ```python
   if "fotos" in fallos_criticos:
       → "Subir 5 fotos con etiquetas EXIF de geolocalización"
   ```

4. **Rating bajo** 🔴 Prioridad 9
   ```python
   if rating < 4.0:
       → "Configurar sistema de respuesta rápida a reseñas negativas"
   ```

5. **Pocas reseñas** 🟡 Prioridad 6
   ```python
   if numero_resenas < 50:
       → "Implementar estrategia de generación de reseñas"
   ```

**Tareas Estándar** (siempre se crean):

- Optimizar descripción con keywords (Prioridad 7)
- Configurar mensajes automáticos (Prioridad 5)
- Verificar horarios de atención (Prioridad 4)
- Crear calendario de posts mensuales (Prioridad 5)
- Seguimiento mes 1 (Prioridad 3)
- Seguimiento mes 2 (Prioridad 2)
- Seguimiento mes 3 (Prioridad 1)

#### Funciones Auxiliares

```python
get_task_completion_percentage(order_id, db)  # Retorna 0-100%
get_pending_tasks_count(order_id, db)          # Cuenta tareas pendientes
get_high_priority_tasks(order_id, db)          # Filtra prioridad >= 7
mark_task_completed(task_id, notes, db)        # Marca completada con timestamp
mark_task_incomplete(task_id, db)              # Revierte completitud
```

## 🔌 API Endpoints

### Base URL: `/api/dashboard`

### 1. Listar Tareas de una Orden

```http
GET /api/dashboard/orders/{order_id}/tasks
```

**Response:**
```json
{
  "tasks": [
    {
      "id": 1,
      "order_id": 5,
      "description": "Reclamar y verificar la propiedad del negocio en Google Business Profile",
      "category": "SEO",
      "is_completed": false,
      "priority": 10,
      "order_index": 1,
      "notes": "El negocio aparece como 'no reclamado' en Google Maps...",
      "created_at": "2024-01-15T10:00:00",
      "completed_at": null
    }
  ],
  "completion_percentage": 25.0,
  "pending_tasks": 9
}
```

### 2. Actualizar Tarea

```http
PATCH /api/dashboard/tasks/{task_id}
```

**Request Body:**
```json
{
  "is_completed": true,
  "notes": "Negocio reclamado exitosamente. Código de verificación recibido por SMS."
}
```

**Response:**
```json
{
  "id": 1,
  "order_id": 5,
  "description": "Reclamar y verificar la propiedad del negocio...",
  "category": "SEO",
  "is_completed": true,
  "priority": 10,
  "order_index": 1,
  "notes": "El negocio aparece como 'no reclamado'...\n\nNegocio reclamado exitosamente...",
  "created_at": "2024-01-15T10:00:00",
  "completed_at": "2024-01-15T14:30:00"
}
```

### 3. Completar Orden

```http
POST /api/dashboard/orders/{order_id}/complete
```

**Request Body:**
```json
{
  "notes": "Cliente muy satisfecho. Score pasó de 35 a 87 en 15 días."
}
```

**Acciones:**
1. ✅ Cambia `order.status` a `COMPLETED`
2. ✅ Establece `order.completed_at` con timestamp
3. ✅ Guarda notas finales
4. ✅ Envía email al cliente notificando finalización

**Response:**
```json
{
  "success": true,
  "message": "Orden 5 completada exitosamente",
  "order_id": 5,
  "completed_at": "2024-01-30T16:45:00",
  "status": "completed"
}
```

## 🔄 Flujo Completo del Sistema

### 1. Cliente Paga el Servicio ($99)

```
Frontend → POST /api/payments/create-checkout-session
         ↓
Stripe Checkout Session creada
         ↓
Cliente paga con tarjeta
         ↓
Stripe Webhook: checkout.session.completed
```

### 2. Webhook Procesa el Pago

```python
# stripe_payments.py
def _handle_checkout_completed(session, db):
    # 1. Actualiza Lead a CLIENTE
    lead.customer_status = CustomerStatus.CLIENTE
    lead.paid_at = datetime.utcnow()
    
    # 2. Actualiza Order a COMPLETED (= pagada)
    order.status = OrderStatus.COMPLETED
    order.completed_at = datetime.utcnow()
    
    # 3. 🚀 GENERA TAREAS AUTOMÁTICAMENTE
    tasks_created = generate_tasks_from_audit(
        order_id=order.id,
        audit_data=lead.audit_data,
        fallos_criticos=lead.fallos_criticos,
        db=db
    )
    
    # 4. Notifica al equipo (TODO: Slack/Email)
```

### 3. Equipo Trabaja las Tareas

```
Dashboard Frontend → GET /api/dashboard/orders/{id}/tasks
                   ↓
Muestra lista de tareas priorizadas
                   ↓
Trabajador marca tarea como completada
                   ↓
PATCH /api/dashboard/tasks/{task_id}
{ "is_completed": true, "notes": "..." }
```

### 4. Cierre del Proyecto

```
Todas las tareas completadas
         ↓
POST /api/dashboard/orders/{id}/complete
{ "notes": "Score final: 87/100" }
         ↓
Sistema envía email al cliente
"¡Tu optimización está lista! 🎉"
```

## 📊 Ejemplo Práctico

### Caso: Restaurante "La Trattoria"

**Datos de Auditoría:**
```json
{
  "score_visibilidad": 35,
  "fallos_criticos": [
    "perfil no reclamado",
    "sin sitio web",
    "fotos antiguas o inexistentes"
  ],
  "audit_data": {
    "rating": 3.8,
    "numero_resenas": 12
  }
}
```

**Tareas Generadas Automáticamente:**

1. 🔴 **[SEO]** Reclamar y verificar propiedad del negocio (Prioridad 10)
2. 🔴 **[SEO]** Configurar sistema de respuesta a reseñas negativas (Prioridad 9)
3. 🟠 **[CONTENIDO]** Crear landing page SEO optimizada (Prioridad 8)
4. 🟡 **[CONTENIDO]** Subir 5 fotos con geoetiquetado (Prioridad 7)
5. 🟡 **[SEO]** Optimizar descripción con keywords (Prioridad 7)
6. 🟡 **[SEO]** Implementar estrategia de reseñas (Prioridad 6)
7. 🟢 **[VERIFICACION]** Configurar mensajes automáticos (Prioridad 5)
8. 🟢 **[CONTENIDO]** Crear calendario de posts (Prioridad 5)
9. 🟢 **[VERIFICACION]** Verificar horarios (Prioridad 4)
10. 🔵 **[VERIFICACION]** Seguimiento mes 1 (Prioridad 3)
11. 🔵 **[VERIFICACION]** Seguimiento mes 2 (Prioridad 2)
12. 🔵 **[VERIFICACION]** Seguimiento mes 3 (Prioridad 1)

**Total: 12 tareas generadas**

## ⚠️ IMPORTANTE: Migración de Base de Datos

La tabla `tasks` NO existe todavía en `lokigi.db`. Necesitas:

### Opción 1: Recrear la base de datos (solo desarrollo)

```bash
# Eliminar DB actual
rm lokigi.db

# Reiniciar el servidor
python main.py
```

### Opción 2: Usar Alembic (producción)

```bash
# Instalar Alembic
pip install alembic

# Inicializar
alembic init alembic

# Generar migración
alembic revision --autogenerate -m "Add tasks table"

# Aplicar migración
alembic upgrade head
```

## 🧪 Testing

### Test Manual con cURL

```bash
# 1. Obtener tareas de una orden
curl http://localhost:8000/api/dashboard/orders/1/tasks

# 2. Marcar tarea como completada
curl -X PATCH http://localhost:8000/api/dashboard/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"is_completed": true, "notes": "Tarea completada exitosamente"}'

# 3. Completar orden
curl -X POST http://localhost:8000/api/dashboard/orders/1/complete \
  -H "Content-Type: application/json" \
  -d '{"notes": "Proyecto finalizado. Cliente satisfecho."}'
```

## 📁 Archivos Modificados/Creados

### ✅ Creados:
- `task_generator.py` (318 líneas) - Lógica de negocio para tareas

### ✅ Modificados:
- `models.py` - Agregado `Task` model y `TaskCategory` enum
- `api_dashboard.py` - Agregados 3 nuevos endpoints
- `stripe_payments.py` - Integración de generación automática de tareas

## 🚀 Próximos Pasos

1. **Migrar la base de datos** para crear tabla `tasks`
2. **Probar el flujo completo** con un pago de prueba en Stripe
3. **Integrar email service** (SendGrid/Mailgun) para notificaciones reales
4. **Actualizar frontend** del dashboard para mostrar tareas reales
5. **Agregar notificaciones** al equipo (Slack/Discord) cuando hay nuevas órdenes

## 📧 Email de Completitud

Cuando se llama a `POST /orders/{id}/complete`, se envía este email:

```
Asunto: ¡Tu negocio {nombre} ya está optimizado! 🎉

Hola {cliente},

¡Excelentes noticias! 🎉

Tu negocio '{nombre_negocio}' ya está completamente optimizado para búsquedas locales.

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
```

---

**Documentación generada el 2024-01-15**
**Sistema Lokigi v2.0 - Dashboard Operativo**
