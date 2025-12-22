# 📊 Esquema de Base de Datos - Lokigi (Supabase PostgreSQL)

## 🎯 Resumen Ejecutivo

Base de datos diseñada para **presupuesto cero** usando Supabase (PostgreSQL free tier: 500MB).

### Stack
- **ORM**: SQLAlchemy
- **Base de Datos**: Supabase PostgreSQL
- **Migraciones**: Alembic (opcional)
- **Costo**: $0/mes (free tier)

---

## 📋 Tablas del Sistema

### 1. **users** - Usuarios del Backoffice

Almacena credenciales y roles de los usuarios internos (Workers y Superusers).

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| **id** | Integer | NO | AUTO | Primary Key |
| **email** | String | NO | - | Email único (index) |
| **hashed_password** | String | NO | - | Password hasheado con bcrypt |
| **full_name** | String | NO | - | Nombre completo del usuario |
| **role** | Enum(UserRole) | NO | WORKER | Rol: SUPERUSER o WORKER |
| **is_active** | Boolean | NO | TRUE | Si el usuario está activo |
| **created_at** | DateTime | NO | NOW() | Fecha de creación |
| **last_login** | DateTime | YES | NULL | Última vez que hizo login |

#### Enums
```python
class UserRole(str, enum.Enum):
    SUPERUSER = "superuser"  # Acceso total al dashboard
    WORKER = "worker"        # Solo acceso al Work Queue
```

#### Índices
- `email` (unique, index)

#### Relaciones
- Ninguna

---

### 2. **leads** - Leads/Clientes

Almacena información de usuarios que completan el formulario de análisis.

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| **id** | Integer | NO | AUTO | Primary Key |
| **nombre** | String | NO | - | Nombre del contacto |
| **email** | String | NO | - | Email único (index) |
| **telefono** | String | NO | - | Teléfono de contacto |
| **whatsapp** | String | YES | NULL | Número de WhatsApp |
| **nombre_negocio** | String | NO | - | Nombre del negocio auditado (index) |
| **score_visibilidad** | Integer | YES | NULL | Lokigi Score (0-100) |
| **fallos_criticos** | JSON | YES | NULL | Array de problemas detectados |
| **audit_data** | JSON | YES | NULL | Datos completos de auditoría |
| **customer_status** | Enum(CustomerStatus) | NO | LEAD | Estado del cliente |
| **stripe_customer_id** | String | YES | NULL | ID en Stripe (index) |
| **stripe_checkout_session_id** | String | YES | NULL | Última sesión de checkout |
| **stripe_payment_intent_id** | String | YES | NULL | Último payment intent |
| **created_at** | DateTime(TZ) | NO | NOW() | Fecha de creación |
| **updated_at** | DateTime(TZ) | YES | NULL | Última actualización |
| **paid_at** | DateTime(TZ) | YES | NULL | Fecha del primer pago |

#### Enums
```python
class CustomerStatus(str, enum.Enum):
    LEAD = "lead"        # Solo dejó datos
    CLIENTE = "cliente"  # Pagó algún producto
```

#### Índices
- `email` (unique, index)
- `nombre_negocio` (index)
- `stripe_customer_id` (index)

#### Relaciones
- **orders**: One-to-Many con `orders` (back_populates="lead")

#### Ejemplo de `fallos_criticos` JSON
```json
[
  {
    "titulo": "Negocio NO reclamado",
    "descripcion": "Cualquiera puede editar tu información",
    "impacto_economico": "$20,400 USD/mes"
  },
  {
    "titulo": "Rating bajo (3.2)",
    "descripcion": "Espanta al 78% de clientes",
    "impacto_economico": "270% menos clics"
  }
]
```

#### Ejemplo de `audit_data` JSON
```json
{
  "lokigi_score": 45,
  "dimensions": {
    "Propiedad": 10,
    "Reputación": 15,
    "Contenido Visual": 8,
    "Presencia Digital": 12
  },
  "lucro_cesante": {
    "mensual_usd": 12500,
    "anual_usd": 150000,
    "clientes_perdidos_mes": 500
  },
  "posicion_estimada": 7,
  "recomendaciones": [
    "1️⃣ ACCIÓN INMEDIATA: Reclama tu negocio en Google My Business",
    "2️⃣ URGENTE: Implementa sistema para pedir reseñas"
  ]
}
```

---

### 3. **orders** - Órdenes de Compra

Registra todas las compras realizadas (e-book $9 o servicio completo $99).

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| **id** | Integer | NO | AUTO | Primary Key |
| **lead_id** | Integer | NO | - | Foreign Key → leads.id (index) |
| **product_type** | Enum(ProductType) | NO | - | Tipo de producto (index) |
| **amount** | Float | NO | - | Monto pagado en USD |
| **currency** | String | NO | usd | Moneda (siempre USD) |
| **stripe_session_id** | String | NO | - | ID de sesión de Stripe (unique, index) |
| **stripe_payment_intent_id** | String | YES | NULL | ID de payment intent (index) |
| **status** | Enum(OrderStatus) | NO | PENDING | Estado de la orden (index) |
| **download_link** | String | YES | NULL | Link de descarga del e-book |
| **notes** | Text | YES | NULL | Notas internas del equipo |
| **created_at** | DateTime(TZ) | NO | NOW() | Fecha de creación |
| **completed_at** | DateTime(TZ) | YES | NULL | Fecha de completado |

#### Enums
```python
class ProductType(str, enum.Enum):
    EBOOK = "ebook"      # E-book $9
    SERVICE = "service"  # Servicio completo $99

class OrderStatus(str, enum.Enum):
    PENDING = "pending"       # Recién creada
    PAID = "paid"             # Pago confirmado (DEPRECATED - usar COMPLETED)
    IN_PROGRESS = "in_progress"  # Workers trabajando en ella
    COMPLETED = "completed"   # Finalizada y entregada
    CANCELLED = "cancelled"   # Cancelada
```

#### Índices
- `lead_id` (foreign key, index)
- `product_type` (index)
- `stripe_session_id` (unique, index)
- `stripe_payment_intent_id` (index)
- `status` (index)

#### Relaciones
- **lead**: Many-to-One con `leads` (back_populates="orders")
- **tasks**: One-to-Many con `tasks` (cascade="all, delete-orphan")

#### Flujo de Estados
```
PENDING → IN_PROGRESS → COMPLETED
   ↓
CANCELLED
```

---

### 4. **tasks** - Tareas Operativas

Tareas que deben completar los Workers para cada orden de servicio ($99).

| Campo | Tipo | Null | Default | Descripción |
|-------|------|------|---------|-------------|
| **id** | Integer | NO | AUTO | Primary Key |
| **order_id** | Integer | NO | - | Foreign Key → orders.id (index) |
| **description** | Text | NO | - | Descripción de la tarea |
| **category** | Enum(TaskCategory) | NO | - | Categoría de la tarea (index) |
| **is_completed** | Boolean | NO | FALSE | Si está completada (index) |
| **priority** | Integer | NO | 0 | Mayor número = mayor prioridad |
| **order_index** | Integer | NO | 0 | Orden de visualización |
| **notes** | Text | YES | NULL | Notas del equipo |
| **created_at** | DateTime(TZ) | NO | NOW() | Fecha de creación |
| **completed_at** | DateTime(TZ) | YES | NULL | Fecha de completado |

#### Enums
```python
class TaskCategory(str, enum.Enum):
    SEO = "seo"                  # Optimización SEO
    CONTENIDO = "contenido"      # Creación de contenido, fotos
    VERIFICACION = "verificacion"  # Revisión de cambios
```

#### Índices
- `order_id` (foreign key, index)
- `category` (index)
- `is_completed` (index)

#### Relaciones
- **order**: Many-to-One con `orders` (back_populates="tasks")

#### Ejemplo de Tareas Generadas
Para un servicio completo ($99):
```python
[
  {
    "description": "Reclamar perfil de Google My Business",
    "category": "SEO",
    "priority": 10,
    "order_index": 1
  },
  {
    "description": "Subir 20 fotos profesionales del negocio",
    "category": "CONTENIDO",
    "priority": 8,
    "order_index": 2
  },
  {
    "description": "Optimizar categorías y descripción",
    "category": "SEO",
    "priority": 7,
    "order_index": 3
  },
  {
    "description": "Verificar NAP consistency",
    "category": "VERIFICACION",
    "priority": 5,
    "order_index": 4
  }
]
```

---

## 🔗 Diagrama de Relaciones

```
┌─────────────┐
│    users    │
│ (backoffice)│
└─────────────┘
     (no relations)

┌─────────────┐
│    leads    │ 1──┐
│  (clientes) │    │
└─────────────┘    │
                   │ 1:N
                   ↓
               ┌─────────────┐
               │   orders    │ 1──┐
               │  (compras)  │    │
               └─────────────┘    │ 1:N
                                  ↓
                              ┌─────────────┐
                              │    tasks    │
                              │  (trabajo)  │
                              └─────────────┘
```

### Ejemplo de Relación Completa
```
Lead (id=1, email="dueno@pizzeria.com")
  ↓
Order (id=1, product_type="SERVICE", amount=99)
  ↓
Tasks:
  - Task (id=1, description="Reclamar GMB", is_completed=True)
  - Task (id=2, description="Subir fotos", is_completed=True)
  - Task (id=3, description="Optimizar categorías", is_completed=False)
```

---

## 🔍 Queries Comunes

### 1. Obtener Lead con sus órdenes
```python
from sqlalchemy.orm import Session
from models import Lead, Order

def get_lead_with_orders(email: str, db: Session):
    return db.query(Lead)\
        .filter(Lead.email == email)\
        .first()
    # Acceso: lead.orders (relación cargada)
```

### 2. Obtener órdenes pendientes con tareas
```python
def get_pending_orders(db: Session):
    return db.query(Order)\
        .filter(Order.status == OrderStatus.IN_PROGRESS)\
        .order_by(Order.created_at.desc())\
        .all()
    # Acceso: order.tasks, order.lead
```

### 3. Estadísticas de conversión
```python
def get_conversion_stats(db: Session):
    total_leads = db.query(Lead).count()
    total_clientes = db.query(Lead)\
        .filter(Lead.customer_status == CustomerStatus.CLIENTE)\
        .count()
    
    conversion_rate = (total_clientes / total_leads) * 100
    
    return {
        "total_leads": total_leads,
        "total_clientes": total_clientes,
        "conversion_rate": conversion_rate
    }
```

### 4. Leads por país (Analytics)
```python
from sqlalchemy import func

def get_leads_by_country(db: Session):
    return db.query(
        Lead.pais,
        func.count(Lead.id).label('count')
    )\
    .group_by(Lead.pais)\
    .order_by(func.count(Lead.id).desc())\
    .all()
```

---

## 🚀 Inicialización de Base de Datos

### Script de Inicialización
```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Construcción de DATABASE_URL
DATABASE_URL = f"postgresql://postgres:{SUPABASE_KEY}@{SUPABASE_URL}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Crea todas las tablas si no existen"""
    from models import User, Lead, Order, Task
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Crear tablas
```python
from database import init_db

# En main.py o script de inicialización
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Base de datos inicializada")
```

---

## 📊 Métricas de Uso (Free Tier Supabase)

| Recurso | Límite Free Tier | Uso Estimado | Status |
|---------|------------------|--------------|--------|
| Almacenamiento | 500 MB | ~50 MB | ✅ OK |
| Conexiones | 60 simultáneas | ~10 promedio | ✅ OK |
| Rows (estimado) | Ilimitadas | ~10,000 leads/año | ✅ OK |
| Bandwidth | 2 GB/mes | ~500 MB/mes | ✅ OK |

### Cálculo de Crecimiento
```
Tamaño promedio por Lead: 5 KB
10,000 leads = 50 MB

Tamaño promedio por Order: 2 KB
5,000 orders = 10 MB

Tamaño promedio por Task: 1 KB
20,000 tasks = 20 MB

TOTAL ESTIMADO: ~80 MB (16% del free tier)
```

**Conclusión:** El free tier de Supabase es más que suficiente para los primeros 10,000 clientes.

---

## 🔐 Seguridad y Buenas Prácticas

### 1. Variables de Entorno
```bash
# .env
SUPABASE_URL=db.your-project.supabase.co
SUPABASE_KEY=your-secret-key
DATABASE_URL=postgresql://postgres:${SUPABASE_KEY}@${SUPABASE_URL}
```

### 2. Índices Críticos
Los siguientes índices están creados para optimizar queries frecuentes:
- `leads.email` (unique) - Búsqueda de leads
- `leads.nombre_negocio` - Búsqueda por negocio
- `orders.status` - Filtrado de órdenes
- `tasks.is_completed` - Work Queue

### 3. Cascade Delete
```python
# En Order model
tasks = relationship("Task", cascade="all, delete-orphan")

# Esto significa: Si eliminas una Order, se eliminan sus Tasks automáticamente
```

### 4. Timestamps Automáticos
```python
created_at = Column(DateTime(TZ), server_default=func.now())
updated_at = Column(DateTime(TZ), onupdate=func.now())
```

---

## 📝 Checklist de Implementación

- [x] Modelo `User` con roles SUPERUSER/WORKER
- [x] Modelo `Lead` con campos de auditoría y Stripe
- [x] Modelo `Order` con estados y productos
- [x] Modelo `Task` con categorías y prioridades
- [x] Relaciones definidas (Lead → Orders → Tasks)
- [x] Índices para queries frecuentes
- [x] Enums para estados y categorías
- [x] Timestamps con timezone
- [x] Cascade delete configurado
- [x] Documentación completa del esquema

---

## 🎯 Próximos Pasos

1. **Migraciones con Alembic** (opcional)
   ```bash
   alembic init alembic
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

2. **Backup Automático**
   - Supabase incluye backups diarios automáticos
   - Configurar punto de restauración semanal

3. **Monitoreo**
   - Dashboard de Supabase muestra uso en tiempo real
   - Alertas cuando se acerque al 80% del free tier

**Estado:** ✅ **SCHEMA COMPLETO Y DOCUMENTADO**
