# Lokigi - Local SEO Auditor 🚀

Sistema completo de auditoría automática de SEO Local con Lead Generation, pagos con Stripe y base de datos.

## 🎯 Características

- ✅ **Lead Generation** - Captura email y teléfono antes de mostrar resultados
- ✅ **Análisis automático** con OpenAI (GPT-4)
- ✅ **Lógica de negocio** - Oferta de Plan Express ($9) si score < 50
- ✅ **Base de datos SQLAlchemy** - Gestión completa de leads y pagos
- ✅ **Integración Stripe** - Checkout y webhooks
- ✅ **Estados de pago** - Pending, Paid, Delivered
- ✅ **Frontend Next.js 14** - Flujo completo de conversión

## 🏗️ Arquitectura

```
lokigi/
├── Backend (FastAPI)
│   ├── main.py              # API endpoints
│   ├── database.py          # Configuración DB
│   ├── models.py            # Modelo Lead
│   ├── schemas.py           # Validación Pydantic
│   └── stripe_service.py    # Lógica de Stripe
│
└── Frontend (Next.js 14)
    ├── app/
    │   ├── page.tsx         # Formulario Lead
    │   ├── audit/[id]/      # Resultados
    │   └── success/         # Confirmación pago
    └── components/
        ├── LeadForm.tsx
        ├── AuditResults.tsx
        ├── CTACard.tsx
        └── ...
```

## 🚀 Instalación

### Backend

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Edita .env con tus keys:
# - OPENAI_API_KEY
# - STRIPE_SECRET_KEY
# - STRIPE_WEBHOOK_SECRET

# Ejecutar servidor
python main.py
```

Backend disponible en: `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponible en: `http://localhost:3000`

## 📊 Base de Datos

### Modelo Lead

```python
class Lead(Base):
    id: int
    email: str
    telefono: str
    nombre_negocio: str
    
    # Datos auditoría
    rating: float
    numero_resenas: int
    tiene_sitio_web: bool
    fecha_ultima_foto: str
    score_visibilidad: int
    fallos_criticos: JSON
    
    # Pagos
    payment_status: Enum (pending, paid, delivered, failed)
    stripe_payment_intent_id: str
    stripe_checkout_session_id: str
    
    # Ofertas
    oferta_plan_express: bool
    plan_express_accepted: bool
    
    # Timestamps
    created_at, updated_at, paid_at, delivered_at
```

La base de datos SQLite se crea automáticamente en `lokigi.db`

## 🔄 Flujo Completo

### 1. Lead Generation
- Usuario ingresa: Email, Teléfono, Nombre del negocio
- Se crea Lead en DB con `payment_status = PENDING`
- Se genera auditoría con OpenAI

### 2. Auditoría
- OpenAI analiza el negocio
- Se calcula `score_visibilidad`
- Si `score < 50` → `oferta_plan_express = True`

### 3. Oferta Plan Express
- Solo visible si score < 50
- Botón "Arreglar ahora por $9"
- Click → Crea sesión Stripe Checkout

### 4. Checkout Stripe
- Usuario redirigido a Stripe
- Paga $9 por Plan de Acción Express
- Stripe envía webhook a `/api/stripe/webhook`

### 5. Webhook Processing
```
checkout.session.completed → payment_status = PAID
payment_intent.failed → payment_status = FAILED
```

### 6. Confirmación
- Redirect a `/success`
- Email confirmación (por implementar)
- Generación PDF (por implementar)
- `payment_status = DELIVERED` (manual/automático)

## 📡 API Endpoints

### Backend

```bash
POST /api/leads
# Crea lead y genera auditoría
Body: { email, telefono, nombre_negocio }
Response: { id, email, score_visibilidad, ... }

GET /api/leads/{lead_id}/audit
# Obtiene resultados completos
Response: { lead, datos_analizados, reporte, oferta_plan_express }

POST /api/leads/{lead_id}/checkout
# Crea sesión Stripe
Response: { checkout_url, session_id }

POST /api/stripe/webhook
# Recibe eventos de Stripe (checkout.session.completed, etc.)
```

## 🔧 Configuración Stripe

### 1. Obtener Keys
```bash
# Dashboard: https://dashboard.stripe.com
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 2. Configurar Webhook
```bash
# En Stripe Dashboard > Developers > Webhooks
URL: https://tu-dominio.com/api/stripe/webhook

Eventos:
- checkout.session.completed
- payment_intent.payment_failed
```

### 3. Testing Local
```bash
# Usar Stripe CLI
stripe listen --forward-to localhost:8000/api/stripe/webhook

# En otro terminal
stripe trigger checkout.session.completed
```

## 🎨 Frontend - Flujo de Pantallas

### 1. `/` - Lead Form
- Formulario de captura
- Validación email/teléfono
- Loading state
- Redirect a `/audit/{id}`

### 2. `/audit/{id}` - Resultados
- Score de salud circular
- 3 fallos críticos
- Comparativa vs competencia
- CTA Plan Express (si score < 50)

### 3. `/success` - Confirmación
- Animación éxito
- Qué sigue (email, PDF, dashboard)
- Auto-redirect en 10s

## 🧪 Testing

### Test Backend
```bash
# Test crear lead
curl -X POST http://localhost:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","telefono":"+34612345678","nombre_negocio":"Test Restaurant"}'

# Test obtener auditoría
curl http://localhost:8000/api/leads/1/audit
```

### Test Stripe
```bash
# Tarjeta de prueba
Número: 4242 4242 4242 4242
Fecha: cualquier futura
CVC: cualquier 3 dígitos
```

## 🔐 Seguridad

- ✅ CORS configurado para frontend
- ✅ Validación Stripe signature en webhooks
- ✅ Validación Pydantic en todos los endpoints
- ✅ Email único por lead
- ⚠️ TODO: Rate limiting
- ⚠️ TODO: Autenticación para dashboard admin

## 📈 Próximas Funcionalidades

- [ ] Generación automática PDF con plan de acción
- [ ] Email transaccional (confirmación, entrega PDF)
- [ ] Dashboard admin para ver leads
- [ ] Analytics (conversión, revenue, etc.)
- [ ] Integración Google My Business API (auditoría real)
- [ ] Multi-tenancy (múltiples negocios por usuario)
- [ ] A/B testing del pricing
- [ ] Seguimiento post-venta

## 🛠️ Stack Tecnológico

**Backend:**
- FastAPI - Web framework
- SQLAlchemy - ORM
- Stripe - Pagos
- OpenAI GPT-4 - IA análisis
- SQLite - Base de datos (cambiar a PostgreSQL en prod)

**Frontend:**
- Next.js 14 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Recharts - Gráficos
- Lucide React - Iconos

## 📄 Licencia

MIT

---

Made with ❤️ by Lokigi Team
