# 🏗️ ARQUITECTURA LOKIGI - Sistema Completo

## 📚 Índice
1. [Stack Tecnológico](#stack-tecnológico)
2. [Estructura Backend (FastAPI)](#estructura-backend)
3. [Estructura Frontend (Next.js 14)](#estructura-frontend)
4. [Flujo de Datos](#flujo-de-datos)
5. [APIs y Endpoints](#apis-y-endpoints)
6. [Componentes Clave](#componentes-clave)

---

## 🚀 Stack Tecnológico

### Backend
- **Framework:** FastAPI 0.104+
- **Database:** Supabase (PostgreSQL)
- **ORM:** SQLAlchemy 2.0
- **AI:** Google Gemini AI (capa gratuita) + OpenAI GPT-4
- **Payments:** Stripe API
- **Auth:** JWT (python-jose)
- **i18n:** Middleware custom de detección por IP

### Frontend
- **Framework:** Next.js 14 (App Router)
- **UI:** React 19 + TypeScript
- **Styling:** Tailwind CSS
- **Charts:** Recharts 2.12
- **Icons:** Lucide React
- **Forms:** React Hook Form + Zod

### Infrastructure
- **Hosting:** Vercel (Frontend) + Railway/Render (Backend)
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry
- **Analytics:** PostHog

---

## 🗂️ Estructura Backend (FastAPI)

```
lokigi/
├── main.py                      # 🎯 Entry point - FastAPI app
├── database.py                  # 🗄️ Supabase connection + SQLAlchemy engine
├── models.py                    # 📊 Database models (443 líneas)
├── schemas.py                   # 📋 Pydantic schemas (500+ líneas)
├── auth.py                      # 🔐 JWT authentication
├── middleware_i18n.py           # 🌍 Language detection middleware
│
├── API Routers:
│   ├── api_v1.py                # 🎯 /api/v1/* - Motor de análisis principal
│   ├── api_auth.py              # 🔑 /api/auth/* - Login/Register/Logout
│   ├── api_payments.py          # 💳 /api/payments/* - Stripe checkout
│   ├── api_dashboard.py         # 📊 /api/dashboard/* - Métricas + Command Center
│   ├── api_customer_portal.py  # 👤 /api/customer/* - Portal del cliente
│   ├── api_retention.py         # 🛡️ /api/retention/* - Exit Flow Anti-Churn
│   ├── api_radar.py             # 📡 /api/radar/* - Monitoreo de competidores
│   ├── api_data_quality.py      # ✅ /api/data-quality/* - Validación NAP
│   └── api_lokigi_score.py      # 🎯 /api/lokigi-score/* - Algoritmo de scoring
│
├── Services:
│   ├── stripe_service.py        # 💳 Lógica de Stripe
│   ├── stripe_payments.py       # 💰 Gestión de pagos
│   ├── analyzer_service.py      # 🔍 Motor de análisis SEO
│   └── task_generator.py        # 📝 Generador de tareas para workers
│
├── Scripts:
│   ├── recreate_db.py           # 🔄 Recrear database
│   ├── create_users.py          # 👥 Crear usuarios de prueba
│   ├── test_api.py              # 🧪 Tests de endpoints
│   ├── test_payments.py         # 💳 Tests de Stripe
│   └── test_tasks.py            # ✅ Tests de tareas
│
└── Documentation:
    ├── README.md                # 📖 Documentación principal
    ├── MVP_README.md            # 🚀 Guía del MVP
    ├── SETUP.md                 # ⚙️ Setup inicial
    ├── FLOW.md                  # 🔄 Flujo de trabajo
    ├── GUIA_DE_USO.md           # 📘 Guía de uso
    ├── AUTHENTICATION_SYSTEM.md # 🔐 Sistema de autenticación
    ├── DASHBOARD_OPERATIVO.md   # 📊 Dashboard operativo
    ├── WORK_DASHBOARD_FRONTEND.md # 💼 Dashboard de workers
    ├── MONETIZATION_IMPLEMENTED.md # 💰 Sistema de monetización
    ├── PAYMENTS_GUIDE.md        # 💳 Guía de pagos
    ├── STRIPE_SETUP.md          # 💰 Setup de Stripe
    └── LOKIGI_MASTER_MANUAL.md  # 📘 Manual de procedimientos
```

---

## 🎨 Estructura Frontend (Next.js 14)

```
frontend/
├── src/
│   ├── app/                     # 📱 App Router (Next.js 14)
│   │   ├── layout.tsx           # 🎨 Layout principal
│   │   ├── page.tsx             # 🏠 Landing page
│   │   ├── globals.css          # 🎨 Estilos globales (Tailwind)
│   │   │
│   │   ├── audit/               # 🔍 Análisis y reportes
│   │   │   └── [id]/
│   │   │       └── page.tsx     # 📊 Vista de auditoría individual
│   │   │
│   │   ├── audit-results/
│   │   │   └── page.tsx         # 📋 Lista de auditorías
│   │   │
│   │   ├── report/              # 📊 Reportes detallados
│   │   │   └── [id]/
│   │   │       └── page.tsx     # 🎯 ReportCard + Heatmap
│   │   │
│   │   ├── dashboard/           # 📊 Dashboards
│   │   │   ├── page.tsx         # 🏠 Dashboard principal
│   │   │   ├── work/
│   │   │   │   └── page.tsx     # 💼 Work Queue (Workers)
│   │   │   ├── orders/
│   │   │   │   ├── page.tsx     # 📦 Lista de órdenes
│   │   │   │   └── [orderId]/
│   │   │   │       └── page.tsx # 📄 Detalle de orden
│   │   │   └── command-center/
│   │   │       └── page.tsx     # ⚡ BI Dashboard (800+ líneas)
│   │   │
│   │   ├── backoffice/
│   │   │   └── page.tsx         # 🔧 Admin backoffice
│   │   │
│   │   └── success/
│   │       └── page.tsx         # ✅ Página de éxito post-pago
│   │
│   ├── components/              # 🧩 Componentes reutilizables
│   │   ├── ReportCard.tsx       # 📊 Tarjeta de reporte (NUEVO)
│   │   ├── AuditResults.tsx     # 📋 Resultados de auditoría
│   │   ├── AuthGuard.tsx        # 🔐 Guard de autenticación
│   │   ├── ComparisonTable.tsx  # 📊 Tabla de comparación
│   │   ├── CriticalPoints.tsx   # ⚠️ Puntos críticos
│   │   ├── CTACard.tsx          # 📢 Call-to-action cards
│   │   ├── HealthScoreChart.tsx # 📈 Gráfico de score
│   │   ├── LeadCaptureModal.tsx # 🎯 Modal de captura de leads
│   │   ├── LeadForm.tsx         # 📝 Formulario de leads
│   │   ├── LogoutButton.tsx     # 🚪 Botón de logout
│   │   ├── CancellationFlow.tsx # 🛡️ Exit Flow Anti-Churn (600+ líneas)
│   │   │
│   │   ├── audit/               # 🔍 Componentes de auditoría
│   │   │   ├── CriticalAlertsGrid.tsx
│   │   │   ├── LocalComparison.tsx
│   │   │   ├── MoneyAtRisk.tsx
│   │   │   ├── ScoreGauge.tsx
│   │   │   └── StickyCTA.tsx
│   │   │
│   │   └── dashboard/           # 📊 Componentes de dashboard
│   │       └── DashboardSidebar.tsx
│   │
│   └── lib/
│       └── utils.ts             # 🛠️ Utilidades (cn, clsx)
│
├── public/                      # 📁 Assets estáticos
├── package.json                 # 📦 Dependencies
├── tailwind.config.ts           # 🎨 Tailwind config (theme cyber)
├── tsconfig.json                # 📝 TypeScript config
└── next.config.mjs              # ⚙️ Next.js config
```

---

## 🔄 Flujo de Datos

### 1. **Lead Capture (Captura de Lead)**

```
Usuario → Landing Page → LeadForm.tsx
  ↓
POST /api/v1/create-lead
  ↓
Database (leads table)
  ↓
Análisis automático (background job)
  ↓
POST /api/v1/analyze
  ↓
Google Gemini AI / OpenAI
  ↓
Lokigi Score + Lucro Cesante
  ↓
Email automático con reporte
```

### 2. **Checkout Flow (Flujo de Pago)**

```
Usuario ve reporte → Click "Comprar Servicio"
  ↓
POST /api/payments/create-checkout
  ↓
Stripe Checkout Session
  ↓
Usuario paga en Stripe
  ↓
Webhook: POST /api/payments/webhook
  ↓
payment_status = PAID
  ↓
Orden asignada a Worker
  ↓
Worker completa orden
  ↓
Email de éxito al cliente
```

### 3. **Exit Flow Anti-Churn (Retención)**

```
Usuario click "Cancelar" → CancellationFlow.tsx
  ↓
PASO 1: POST /api/retention/micro-audit
  ↓
Detecta amenazas de competidores
  ↓
Modal con urgency_message
  ↓
Usuario persiste → PASO 2
  ↓
POST /api/retention/retention-offer
  ↓
Genera cupón 50% OFF en Stripe
  ↓
Usuario acepta → POST /api/retention/apply-coupon
  ↓
Suscripción salvada ✅
  ↓
Usuario rechaza → PASO 3
  ↓
POST /api/retention/churn-feedback
  ↓
Guarda motivo en ChurnFeedback table
  ↓
Suscripción cancelada 😢
```

### 4. **Command Center Dashboard (BI)**

```
Admin → /dashboard/command-center
  ↓
Promise.all([
  GET /api/dashboard/command-center/financial,
  GET /api/dashboard/command-center/funnel,
  GET /api/dashboard/command-center/workers,
  GET /api/dashboard/command-center/heatmap
])
  ↓
Renderiza 4 secciones:
  1. Financial Overview (Recharts BarChart)
  2. Conversion Funnel (Progress bars + alertas)
  3. Worker Performance (Tabla con rankings)
  4. Geographical Heatmap (Mapa con lat/lng)
```

---

## 🎯 APIs y Endpoints

### **Motor de Análisis Principal**

#### `POST /api/v1/analyze`
**Input:**
```json
{
  "business_name": "Restaurante El Sabor",
  "google_maps_url": "https://maps.google.com/?cid=...",
  "country": "AR"
}
```

**Output:**
```json
{
  "score_visibilidad": 42,
  "lucro_cesante_mensual": 850,
  "lucro_cesante_anual": 10200,
  "fallos_criticos": [
    {
      "titulo": "Perfil Duplicado",
      "descripcion": "Existen 2 perfiles...",
      "impacto_economico": "$850/mes"
    }
  ],
  "business_coordinates": [-34.6037, -58.3816],
  "competitors_nearby": [
    {
      "name": "Restaurante Competencia",
      "distance": 350,
      "score": 68
    }
  ]
}
```

---

### **Command Center (BI Dashboard)**

#### `GET /api/dashboard/command-center/financial`
**Query Params:** `?time_range=30d&country=AR`

**Output:**
```json
{
  "total_revenue": 5420,
  "ebook_revenue": 630,
  "service_revenue": 3960,
  "subscription_revenue": 830,
  "revenue_by_country": [
    {"country": "AR", "revenue": 2100, "orders": 45},
    {"country": "BR", "revenue": 1850, "orders": 38}
  ]
}
```

#### `GET /api/dashboard/command-center/funnel`
**Output:**
```json
{
  "total_visitors": 1520,
  "completed_diagnosis": 1180,
  "initiated_checkout": 420,
  "completed_purchase": 280,
  "visitor_to_diagnosis_rate": 77.6,
  "diagnosis_to_checkout_rate": 35.6,
  "checkout_to_purchase_rate": 66.7,
  "checkout_abandonment_rate": 33.3,
  "overall_conversion_rate": 18.4
}
```

#### `GET /api/dashboard/command-center/workers`
**Output:**
```json
{
  "total_orders": 156,
  "avg_completion_time_hours": 18.5,
  "workers": [
    {
      "worker_name": "Juan Pérez",
      "completed_orders": 42,
      "in_progress_orders": 3,
      "avg_completion_time_hours": 16.2,
      "avg_score_improvement": 22.5,
      "efficiency_score": 87.3
    }
  ]
}
```

#### `GET /api/dashboard/command-center/heatmap`
**Output:**
```json
{
  "total_diagnoses": 1180,
  "top_country": "AR",
  "locations": [
    {
      "country": "AR",
      "country_name": "Argentina",
      "flag": "🇦🇷",
      "diagnoses": 420,
      "leads": 580,
      "conversion_rate": 72.4,
      "latitude": -34.6037,
      "longitude": -58.3816
    }
  ]
}
```

---

### **Retention (Anti-Churn)**

#### `POST /api/retention/micro-audit`
**Input:**
```json
{
  "lead_id": 123,
  "subscription_id": 45,
  "language": "es"
}
```

**Output:**
```json
{
  "has_threats": true,
  "threats_detected": [
    {
      "competitor_name": "Café del Centro",
      "threat_type": "ranking_increase",
      "threat_level": "critical",
      "details": "Subió 3 posiciones y está a solo 2 reseñas de superarte",
      "metric_change": {"rank_position": -3, "reviews_gap": 2}
    }
  ],
  "business_current_rank": 5,
  "total_competitors": 12,
  "urgency_message": "⚠️ ¿Estás seguro? En los últimos 30 días...",
  "risk_level": "high"
}
```

#### `POST /api/retention/retention-offer`
**Output:**
```json
{
  "offer": {
    "offer_type": "discount_50",
    "original_price": 29.0,
    "discount_price": 14.5,
    "coupon_code": "RETENTION_XYZ123",
    "savings_amount": 58.0,
    "valid_until": "2025-12-23T18:00:00Z"
  },
  "persuasion_message": "🎁 Última oportunidad: Quédate 2 meses más al 50% de descuento...",
  "cta_button_text": "✅ Aceptar oferta (50% OFF)"
}
```

---

## 🧩 Componentes Clave

### **ReportCard.tsx** (NUEVO)

Componente principal para visualizar reportes de auditoría con:

**Features:**
- ✅ Circular progress gauge del Lokigi Score
- ✅ Color coding: Verde (80+), Amarillo (60-79), Naranja (40-59), Rojo (<40)
- ✅ Lucro Cesante mensual y anual en cards destacados
- ✅ Grid de fallos críticos con impacto económico
- ✅ Heatmap de competidores cercanos con distancias
- ✅ CTA footer para conversión a Premium
- ✅ Dark theme con neon green (#00ff41)
- ✅ Responsive design
- ✅ Loading states con skeleton

**Props:**
```typescript
interface ReportCardProps {
  leadId: number;
  auditData?: AuditData;
  loading?: boolean;
}
```

**Uso:**
```tsx
<ReportCard leadId={123} />
```

---

### **CancellationFlow.tsx**

Modal de 3 pasos para retención de suscriptores:

**Features:**
- ✅ Paso 1: Micro-Audit con amenazas de competidores
- ✅ Paso 2: Retention Offer con cupón Stripe
- ✅ Paso 3: Churn Feedback survey
- ✅ Traducciones ES/PT/EN
- ✅ Loading states y error handling
- ✅ Dark theme cyber

**Props:**
```typescript
interface CancellationFlowProps {
  isOpen: boolean;
  onClose: () => void;
  subscriptionId: number;
  leadId: number;
  language: "es" | "pt" | "en";
}
```

---

### **Command Center Page** (command-center/page.tsx)

Dashboard ejecutivo de BI con 4 secciones:

**Sección 1: Financial Overview**
- 4 KPI cards: Total Revenue, E-books, Services, Subscriptions
- BarChart de revenue por producto (Recharts)
- Lista de revenue por país con flags

**Sección 2: Conversion Funnel**
- Horizontal BarChart con 4 etapas
- 3 progress bars con tasas de conversión
- Alert si checkout abandonment > 50%

**Sección 3: Worker Performance**
- Cards de métricas: Total orders, Avg completion time
- Tabla con 6 columnas: Worker, Completadas, En Proceso, Tiempo Avg, Score Mejora, Eficiencia
- Ranking con Award icon para top performer

**Sección 4: Geographical Heatmap**
- Cards de resumen: Total diagnoses, Top country
- Lista de locations con flags, diagnoses, conversion rates, lat/lng
- Marketing Intelligence box con recomendaciones

---

## 🎨 Theme: Cyber Neon Dark

### Colores principales:
```css
/* Tailwind config */
colors: {
  'neon': {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#00ff41', /* Main neon green */
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
}
```

### Gradientes:
- `bg-gradient-to-br from-gray-900 to-gray-800`
- `bg-gradient-to-r from-neon-500 to-green-500`
- `bg-gradient-to-br from-gray-950 via-gray-900 to-black`

### Efectos:
- `shadow-2xl shadow-neon-500/20` - Glow effect
- `border border-neon-500` - Neon borders
- `hover:shadow-lg hover:shadow-red-500/20` - Hover effects
- `backdrop-blur-sm` - Glass morphism

---

## 🔐 Autenticación y Autorización

### Sistema RBAC (Role-Based Access Control)

**Roles:**
1. **ADMIN** (Daniel + Fundadores)
   - Acceso total
   - Command Center
   - Métricas financieras
   - Export de datos

2. **WORKER** (Empleados)
   - Solo Work Queue
   - Sin métricas financieras
   - No puede ver ingresos

3. **CUSTOMER** (Clientes)
   - Solo sus reportes
   - Solo sus pagos
   - Radar (si tiene suscripción)

### JWT Flow:
```
POST /api/auth/login
  ↓
{username, password}
  ↓
Verify password (bcrypt)
  ↓
Generate JWT token (30 días)
  ↓
{access_token, token_type, user_role}
  ↓
Store in localStorage
  ↓
Requests con header: Authorization: Bearer <token>
  ↓
Middleware verify_token()
  ↓
Inject current_user in endpoint
```

---

## 📊 Database Schema (Principales Tablas)

### **leads**
- id, email, telefono, nombre_negocio
- score_visibilidad, pais, ciudad
- payment_status, oferta_plan_express
- stripe_customer_id, stripe_checkout_session_id
- created_at, updated_at

### **orders**
- id, lead_id, worker_id (FK)
- product_type (EBOOK, SERVICE)
- status (PENDING, IN_PROGRESS, COMPLETED)
- price, currency
- completed_at, created_at

### **radar_subscriptions**
- id, lead_id (FK)
- status (ACTIVE, TRIAL, CANCELLED)
- stripe_subscription_id, stripe_customer_id
- monthly_price, currency
- trial_start, trial_end
- competitors_to_track (JSON)
- monitoring_frequency_days
- total_alerts_sent, total_heatmaps_generated

### **churn_feedback** (NEW)
- id, lead_id, subscription_id
- reason_category, reason_detail
- satisfaction_score (1-5)
- accepted_retention_offer
- retention_offer_type
- had_active_threats
- days_subscribed, total_alerts_received

### **users**
- id, email, hashed_password
- full_name, role (ADMIN, WORKER, CUSTOMER)
- is_active, created_at

---

## 🚀 Deployment

### Backend (FastAPI)
```bash
# Railway / Render
git push origin main
# Auto-deploy from GitHub

# Environment variables:
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
JWT_SECRET_KEY=...
```

### Frontend (Next.js)
```bash
# Vercel
vercel --prod

# Environment variables:
NEXT_PUBLIC_API_URL=https://api.lokigi.com
```

---

## 📈 Métricas de Negocio

### Revenue Streams:
1. **E-book**: $9 (one-time)
2. **Servicio Premium**: $99 (one-time)
3. **Radar Lokigi**: $29/mes (recurring)

### Conversion Funnel:
- Visitors → Diagnosis: ~77%
- Diagnosis → Checkout: ~36%
- Checkout → Purchase: ~67%
- Overall: ~18%

### Churn Rate:
- Baseline: 5% mensual
- Con Exit Flow: 3% mensual
- Retention offer acceptance: 25%

---

## 🎯 Próximos Pasos

1. **A/B Testing del Exit Flow**
   - Variante A: 50% OFF por 2 meses
   - Variante B: 15 días gratis + reporte premium

2. **Integración con Google Maps API**
   - Scraping automático de datos de negocios
   - Geo-coordinates reales
   - Competitor proximity detection

3. **WhatsApp Automation**
   - Alertas de Radar por WhatsApp
   - Confirmaciones de pago
   - Follow-ups automáticos

4. **PDF Export**
   - Reportes en PDF descargables
   - White-label para clientes

5. **Mobile App**
   - React Native
   - Push notifications
   - Offline mode

---

**Última actualización:** Diciembre 22, 2025  
**Versión:** 1.0.0  
**Mantenido por:** Lokigi Team
