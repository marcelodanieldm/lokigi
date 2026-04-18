# Sistema de Retención y Churn - Implementación Fase 2

Este documento describe la implementación backend del sistema de ciclo de vida del usuario y gestión de churn para Lokigi.

## 📋 Resumen de Cambios (Sesión Actual)

### ✅ Nuevos Archivos Creados

#### 1. **backend/app/telemetry_models.py** (Pydantic Models)
Modelos de validación para:
- `ChurnReasonOption`: Enum con 9 categorías de motivos de cancelación
- `LifecycleEventType`: Enum con 10 eventos del ciclo de vida
- `ChurnSurveyPayload`: Esquema para envíos de encuesta de churn
- `ChurnTelemetrySnapshot`: Métricas de engagement en el momento del churn
- `LifecycleEventPayload`: Log de eventos del ciclo de vida
- `ChurnAlertResponse`: Respuesta de alerta del sistema
- `ChurnAnalyticsResponse`: Dashboard de análisis de churn
- `ChurnCorrelationAnalysis`: Análisis profundo de correlaciones

#### 2. **backend/app/churn_alert_engine.py** (Alert Logic)
Motor de alertas con 4 funciones principales:

```python
async def check_ease_of_use_churn_spike(db, time_window_days=30)
```
- **Alerta PRIMARY**: Si >20% de churn es por "Facilidad de uso"
- Severidad: `HIGH`
- Recomendaciones: Auditoría UX, mejorar documentación, onboarding

```python
async def check_churn_rate_spike(db, baseline_days=60, recent_days=7)
```
- Detecta si tasa de churn reciente >50% por encima del baseline
- Severidad: `CRITICAL`
- Indica: Cambios recientes, downtime, o evento externo

```python
async def check_low_engagement_churn_pattern(db, time_window_days=30)
```
- Si >40% de churn viene de usuarios con baja adopción
- Severidad: `MEDIUM`
- Enfoque: Onboarding, primeros pasos, quick wins

```python
async def check_price_sensitivity_spike(db, time_window_days=30)
```
- >25% usuarios pagarían con descuento O >30% citan precio como razón
- Severidad: `MEDIUM`
- Estrategia: Tiers de precios, freemium, garantía

#### 3. **backend/app/churn_correlation_analysis.py** (Analytics)
Análisis correlacional de churn vs engagement:

```python
async def analyze_churn_correlation(db, time_window_days=30)
```
Para cada motivo de churn:
- Count de usuarios churned
- Días activos promedio ANTES de cancelar
- Tasa de aprobación promedio
- Respuestas IA aprobadas promedio
- % que usó tone selector
- % con baja adopción (<50% aprobación, <7 días)
- Insights clave automáticos

#### 4. **backend/alembic/versions/20260418_0007_add_churn_tracking.py**
Migración Alembic con 4 nuevas tablas PostgreSQL:

**lifecycle_events**: Hitos del usuario
- Índices: (user_id, event_type), created_at

**churn_surveys**: Encuestas de retroalimentación
- Índices: primary_reason, cancellation_date, satisfaction_score
- Enum: 9 razones de cancelación

**churn_telemetry_snapshot**: Métricas en momento de churn
- Captura: reviews procesados, IA responses, tasa aprobación, features usados
- Unique constraint: Un snapshot por usuario
- Índices: approval_rate, active_days_before_cancel

**churn_alerts**: Alertas automatizadas
- Campo `acknowledged_at` para rastrear acción del equipo
- Campo `alert_message` con recomendaciones accionables
- Índices: severity, triggered_at, alert_type, acknowledged_at

### ✅ Modelos SQLAlchemy Actualizados (backend/app/models.py)

```python
class LifecycleEvent(Base):
    """Track user journey milestones"""
    user_id: UUID
    event_type: str  # Enum lifecycle_event_type
    metadata: dict | None

class ChurnSurvey(Base):
    """Qualitative feedback at cancellation"""
    user_id: UUID
    primary_reason: str  # Enum churn_reason
    secondary_reasons: list
    satisfaction_score: int  # 1-5
    free_text_feedback: str
    would_return_if_price_reduction: bool
    reduction_amount_percent: int

class ChurnTelemetrySnapshot(Base):
    """Engagement metrics at churn time"""
    user_id: UUID
    active_days_before_cancel: int
    total_ai_responses_approved: int
    approval_rate: float
    used_tone_selector: bool
    days_subscribed: int

class ChurnAlert(Base):
    """Automated system alerts"""
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    metric_value: float
    threshold_value: float
    alert_message: str  # Con recomendaciones
    acknowledged_at: datetime | None
```

Todas las clases tienen relaciones bidireccionales con `User`.

---

## 🔄 Flujo de Implementación Recomendado

### Paso 1: Ejecutar Migración Alembic
```bash
cd backend
alembic upgrade head
```
Esto crea las 4 tablas y 2 enums en PostgreSQL.

### Paso 2: Crear Endpoints API (main.py)
Pendiente agregar a `backend/app/main.py`:

```python
@app.post("/api/churn/survey")
async def submit_churn_survey(
    payload: ChurnSurveyPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """User submits churn feedback when canceling subscription."""
    # 1. Guardar ChurnSurvey
    # 2. Capturar ChurnTelemetrySnapshot (métricas at this moment)
    # 3. Ejecutar todos los alert checks
    # 4. Disparar webhook a product@lokigi.com si alerts HIGH/CRITICAL

@app.get("/api/churn/analytics")
async def get_churn_analytics(
    days: int = Query(30, ge=1, le=90),
    user: User = Depends(get_current_user),  # Solo admin
    db: Session = Depends(get_db),
):
    """Product team dashboard: alerts, correlations, insights."""
    # 1. Obtener recent alerts (últimos 7 días)
    # 2. Ejecutar analyze_churn_correlation()
    # 3. Retornar ChurnAnalyticsResponse
```

### Paso 3: Frontend - Churn Survey UI
Crear página interactiva en `/starter/churn-survey`:
- 9 radio buttons (ChurnReasonOption)
- Slider satisfaction (1-5)
- Textarea free text feedback
- Checkbox "Would return with discount?"
- Despliega campo descuento % si es True
- POST submit a `/api/churn/survey`

### Paso 4: Daily Alert Job (APScheduler)
En `backend/app/monthly_report_worker.py`:

```python
async def daily_churn_report(db: Session):
    """Run at 08:00 UTC daily."""
    alerts = await run_all_churn_checks(db)
    
    # Filter HIGH/CRITICAL
    critical_alerts = [a for a in alerts if a.severity in ["HIGH", "CRITICAL"]]
    
    if critical_alerts:
        # Send email to product@lokigi.com con:
        # - Alert type + severity
        # - Metric value vs threshold
        # - Recomendaciones en alert_message
        # - Link a dashboard: /admin/churn/analytics
```

### Paso 5: Frontend Dashboard Churn
Página privada `/admin/churn/analytics`:
- Gráfico: Churn by reason (últimos 30 días)
- Tabla: Correlation analysis (active days, approval rate, etc.)
- Alertas: HIGH/CRITICAL con resaltado
- Botón "Acknowledge" para reconocer alertas

---

## 📊 Ejemplos de Alertas

### Ejemplo 1: Spike en "Ease of Use"
```
🚨 HIGH ALERT: 25.3% of churn (23/91) attributed to 'Ease of Use Difficulty' 
in last 30 days.

RECOMMENDED ACTIONS:
1. UX Audit - Review onboarding flow and dashboard navigation
2. Documentation - Improve getting-started guides and tutorials
3. Product - Identify pain points from free-text feedback
4. Support - Increase proactive outreach to new users
```
→ Trigger: `check_ease_of_use_churn_spike()` si >20%

### Ejemplo 2: Spike en Tasa Churn
```
🚨 CRITICAL: Churn rate spiked to 8.2% (baseline: 3.1%, +164%) 
in last 7 days (12 churns from 146 signups).

IMMEDIATE ACTION REQUIRED:
1. Investigate recent changes - deploy, pricing, features
2. Check churn survey feedback for common themes
3. Review system logs for errors or downtime
4. Contact top-churn users for quick feedback
```
→ Trigger: `check_churn_rate_spike()` si >50% aumento

### Ejemplo 3: Baja Adopción
```
⚠️ 52.1% of recent churn (8/15) comes from low-engagement users 
(<50% approval, <7 active days).
```
→ Trigger: `check_low_engagement_churn_pattern()` si >40%

---

## 🔐 Seguridad & Privacidad

- **Telemetría**: Solo se captura EN MOMENTO DE CHURN (no retroactivo)
- **GDPR**: Al borrar user, se cascada delete en todas las tablas de churn
- **Datos sensibles**: `free_text_feedback` truncado a 1000 chars
- **Acceso**: Analytics solo para role="admin"

---

## 📈 Métricas Clave Capturadas

Al momento de cancelación, se registra:

```
active_days_before_cancel    # Días entre signup y churn
last_activity_days_ago       # Días desde última actividad
total_reviews_processed      # Total reviews tocados
total_ai_responses_approved  # Total respuestas aprobadas
approval_rate                # % de aprobación (0-1)
used_tone_selector           # Boolean: usó tone selector
used_sentiment_reports       # Boolean: usó reportes
locations_connected          # Cantidad de ubicaciones
days_subscribed              # Duración de suscripción
```

Estas métricas permiten:
1. **Correlación**: ¿Usuarios con baja approval rate churnan más?
2. **Feature adoption**: ¿Quién usa tone selector tiene mejor retention?
3. **Cohort analysis**: ¿Ciertos cohorts tienen churn más alto?
4. **Insights**: "Los churners con 'ease of use' tuvieron 3.2 días promedio de actividad"

---

## 🚀 Estado de Implementación

| Fase | Componente | Status |
|------|-----------|--------|
| 1 | Modelos Pydantic (telemetry_models.py) | ✅ HECHO |
| 2 | Motor de Alertas (churn_alert_engine.py) | ✅ HECHO |
| 3 | Análisis Correlacional (churn_correlation_analysis.py) | ✅ HECHO |
| 4 | Migración Alembic 0007 | ✅ HECHO |
| 5 | Modelos SQLAlchemy | ✅ HECHO |
| 6 | Endpoints API (/api/churn/survey, /api/churn/analytics) | ⏳ PRÓXIMO |
| 7 | Frontend Survey UI | ⏳ PRÓXIMO |
| 8 | Frontend Analytics Dashboard | ⏳ PRÓXIMO |
| 9 | APScheduler Daily Job | ⏳ PRÓXIMO |
| 10 | Email Alerts to Product Team | ⏳ PRÓXIMO |

---

## 🔗 Archivos Relacionados

- **backend/app/telemetry_models.py** - Pydantic schemas
- **backend/app/churn_alert_engine.py** - Alert logic
- **backend/app/churn_correlation_analysis.py** - Analytics queries
- **backend/app/models.py** - SQLAlchemy ORM (updated)
- **backend/alembic/versions/20260418_0007_add_churn_tracking.py** - DB migration
- **LIFECYCLE_AND_CHURN.md** - Design doc (original)
- **backend/app/main.py** - (Pending: API endpoints)

---

## 💡 Próximos Pasos

1. **Ejecutar migración**: `alembic upgrade head`
2. **Crear endpoints**: POST `/api/churn/survey`, GET `/api/churn/analytics`
3. **Crear tests**: Unit + integration para alert engine
4. **Frontend survey**: UI interactiva para cancelación
5. **Dashboard**: Visualizaciones de churn analytics
6. **Email alerts**: Daily report to product@lokigi.com

---

## ❓ Preguntas Frecuentes

**P: ¿Cuándo se captura el snapshot de telemetría?**
A: En el momento de POST `/api/churn/survey`, no retroactivo.

**P: ¿Qué significa "active_days_before_cancel"?**
A: Días entre signup y fecha de cancelación (desde User.created_at hasta ChurnSurvey.cancellation_date).

**P: ¿Cómo se calcular approval_rate?**
A: total_ai_responses_approved / total_ai_responses_generated (como decimal 0-1).

**P: ¿Se puede cambiar el threshold 20% de churn "ease of use"?**
A: Sí, parámetro configurable en `check_ease_of_use_churn_spike(threshold=0.20)`.

**P: ¿Qué pasa si un usuario no completa la survey?**
A: La cancelación procede sin survey (fallback), pero sin datos cualitativos para análisis.

---

## 📝 Notas de Desarrollo

- Todas las funciones en `churn_alert_engine.py` son `async` - usar con `await`
- Los índices SQL permiten queries rápidas incluso con millones de eventos
- El enum `churn_reason` debe coincidir en Pydantic + SQLAlchemy + Alembic
- Considerar partición de tabla `lifecycle_events` si crece >100M rows
- Para cálculos complejos, considerar materializar vistas en PostgreSQL

