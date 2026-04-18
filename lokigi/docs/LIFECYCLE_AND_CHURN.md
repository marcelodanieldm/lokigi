# Ciclo de Vida y Retención - Lifecycle & Churn Analysis

## Overview

Sistema integral para capturar el ciclo de vida del usuario, trackear razones de desuscripción, correlacionar con patrones de uso, y alertar al equipo de producto sobre problemas críticos (ej: >20% churn por "Dificultad de uso").

## 1. Esquema de Base de Datos

### Tabla: `user_lifecycle_events`
Trackea hitos importantes en la vida del usuario.

```sql
CREATE TABLE user_lifecycle_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lifecycle_user_date ON user_lifecycle_events(user_id, event_date);
CREATE INDEX idx_lifecycle_type ON user_lifecycle_events(event_type);
```

**Event Types**:
- `signup` - Usuario se registra
- `first_connection` - Conecta primera ubicación de Google
- `first_reply_generated` - Genera primera respuesta IA
- `first_reply_approved` - Aprueba primera respuesta
- `onboarding_complete` - Completa onboarding
- `payment_method_added` - Agrega método de pago
- `subscription_activated` - Activa suscripción paga
- `subscription_downgrade` - Degrada plan
- `subscription_paused` - Pausa suscripción
- `churn_initiated` - Inicia flujo de desuscripción

---

### Tabla: `churn_surveys`
Encuesta de desuscripción con feedback estructurado.

```sql
CREATE TABLE churn_surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY_REASON VARCHAR(100) NOT NULL,
    SECONDARY_REASONS TEXT[] DEFAULT '{}',
    SATISFACTION_SCORE INT CHECK (satisfaction_score BETWEEN 1 AND 5),
    FREE_TEXT_FEEDBACK TEXT,
    would_return_if_feature VARCHAR(255),
    would_return_if_price_reduction BOOLEAN,
    reduction_amount_percent INT,
    cancellation_date DATE NOT NULL,
    survey_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_churn_survey_reason ON churn_surveys(primary_reason);
CREATE INDEX idx_churn_survey_date ON churn_surveys(cancellation_date);
```

**Primary Reason Options** (enum):
1. `price_too_high` - Precio muy alto
2. `lack_of_features` - Falta de funcionalidades
3. `ease_of_use_difficulty` - Dificultad de uso ⚠️ (triggers alert if >20%)
4. `switched_competitor` - Cambié a competidor
5. `not_using_enough` - No la usaba lo suficiente
6. `poor_support` - Mal soporte
7. `technical_issues` - Problemas técnicos
8. `personal_reasons` - Razones personales
9. `other` - Otro

**Secondary Reasons** (multiple select):
- Mismo set de opciones que Primary

---

### Tabla: `churn_telemetry_snapshot`
Snapshot de métricas de uso al momento de desuscripción (para correlación).

```sql
CREATE TABLE churn_telemetry_snapshot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    churn_survey_id UUID REFERENCES churn_surveys(id) ON DELETE CASCADE,
    
    -- Engagement metrics
    active_days_before_cancel INT NOT NULL,
    last_activity_days_ago INT,
    total_reviews_processed INT,
    total_ai_responses_generated INT,
    total_ai_responses_approved INT,
    approval_rate DECIMAL(5,2),
    
    -- Feature adoption
    used_tone_selector BOOLEAN,
    used_sentiment_reports BOOLEAN,
    used_manual_approval BOOLEAN,
    locations_connected INT,
    
    -- Temporal data
    days_subscribed INT,
    subscription_plan VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telemetry_user ON churn_telemetry_snapshot(user_id);
CREATE INDEX idx_telemetry_survey ON churn_telemetry_snapshot(churn_survey_id);
```

---

### Tabla: `churn_alerts`
Sistema de alertas automáticas para el equipo de producto.

```sql
CREATE TABLE churn_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    time_window_days INT,
    metric_name VARCHAR(100),
    metric_value DECIMAL(10,2),
    threshold_value DECIMAL(10,2),
    alert_message TEXT,
    details JSONB,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_type ON churn_alerts(alert_type);
CREATE INDEX idx_alerts_severity ON churn_alerts(severity);
CREATE INDEX idx_alerts_triggered ON churn_alerts(triggered_at DESC);
CREATE INDEX idx_alerts_unacknowledged ON churn_alerts(acknowledged_at) WHERE acknowledged_at IS NULL;
```

**Alert Types**:
- `high_churn_difficulty` - >20% churn por "Dificultad de uso"
- `spike_in_churn_rate` - Aumento súbito de tasa de churn
- `high_churn_price_sensitivity` - >25% churn por precio
- `low_approval_rate_churners` - Usuarios con <50% approval rate se van
- `low_engagement_churn` - Usuarios inactivos <7 días antes de cancelar

---

## 2. Eventos de Telemetría (Pydantic Models)

```python
# backend/app/telemetry_models.py

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class ChurnReasonOption(str, Enum):
    PRICE_TOO_HIGH = "price_too_high"
    LACK_OF_FEATURES = "lack_of_features"
    EASE_OF_USE_DIFFICULTY = "ease_of_use_difficulty"
    SWITCHED_COMPETITOR = "switched_competitor"
    NOT_USING_ENOUGH = "not_using_enough"
    POOR_SUPPORT = "poor_support"
    TECHNICAL_ISSUES = "technical_issues"
    PERSONAL_REASONS = "personal_reasons"
    OTHER = "other"

class ChurnSurveyPayload(BaseModel):
    user_id: UUID
    primary_reason: ChurnReasonOption
    secondary_reasons: list[ChurnReasonOption] = []
    satisfaction_score: int  # 1-5
    free_text_feedback: str | None = None
    would_return_if_feature: str | None = None
    would_return_if_price_reduction: bool = False
    reduction_amount_percent: int | None = None

class ChurnTelemetrySnapshot(BaseModel):
    user_id: UUID
    active_days_before_cancel: int
    last_activity_days_ago: int
    total_reviews_processed: int
    total_ai_responses_generated: int
    total_ai_responses_approved: int
    approval_rate: float  # 0.0-1.0
    used_tone_selector: bool
    used_sentiment_reports: bool
    used_manual_approval: bool
    locations_connected: int
    days_subscribed: int
    subscription_plan: str

class LifecycleEventPayload(BaseModel):
    user_id: UUID
    event_type: str
    metadata: dict | None = None
```

---

## 3. Correlación: Churn Reason ↔ Engagement Metrics

### Query: Análisis de Correlación

```sql
-- Correlación entre razón de churn y patrones de uso
SELECT
    cs.primary_reason,
    COUNT(DISTINCT cs.user_id) as churn_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct_of_total,
    
    ROUND(AVG(cts.active_days_before_cancel)::numeric, 1) as avg_active_days,
    ROUND(AVG(cts.approval_rate)::numeric, 2) as avg_approval_rate,
    ROUND(AVG(cts.total_ai_responses_approved)::numeric, 1) as avg_responses_approved,
    
    SUM(CASE WHEN cts.used_tone_selector THEN 1 ELSE 0 END) as count_used_tone,
    ROUND(100.0 * SUM(CASE WHEN cts.used_tone_selector THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_used_tone,
    
    SUM(CASE WHEN cts.approval_rate < 0.5 THEN 1 ELSE 0 END) as count_low_engagement,
    ROUND(100.0 * SUM(CASE WHEN cts.approval_rate < 0.5 THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_low_engagement
    
FROM churn_surveys cs
LEFT JOIN churn_telemetry_snapshot cts ON cs.user_id = cts.user_id
WHERE cs.cancellation_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY cs.primary_reason
ORDER BY churn_count DESC;
```

**Insights Expected**:
- **Ease of Use** (>5%): Bajo approval_rate (< 50%), pocos responses generados
- **Price Too High** (>10%): Alto approval_rate (80%+), usuarios muy activos
- **Not Using Enough** (>15%): Bajo active_days (<10), bajo tone selector adoption
- **Switched Competitor** (>8%): Similar engagement, pero más responses generados

---

## 4. Sistema de Alertas Automáticas

### Lógica 1: Alert if >20% Churn por "Dificultad de Uso"

```python
# backend/app/churn_alert_engine.py

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models import ChurnSurvey, ChurnAlert

async def check_ease_of_use_churn_spike(db: Session, time_window_days: int = 30):
    """
    Dispara alerta si más del 20% de las bajas en los últimos N días
    son por "Dificultad de uso" (ease_of_use_difficulty).
    """
    cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
    
    # Total churn en ventana
    total_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(ChurnSurvey.cancellation_date >= cutoff_date.date())
    ) or 0
    
    if total_churn < 5:  # Threshold mínimo para estadística significativa
        return None
    
    # Churn por dificultad de uso
    ease_of_use_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(
            ChurnSurvey.cancellation_date >= cutoff_date.date(),
            ChurnSurvey.primary_reason == "ease_of_use_difficulty"
        )
    ) or 0
    
    pct_difficulty = (ease_of_use_churn / total_churn * 100) if total_churn > 0 else 0
    
    if pct_difficulty > 20:
        alert = ChurnAlert(
            alert_type="high_churn_difficulty",
            severity="HIGH",
            triggered_at=datetime.utcnow(),
            time_window_days=time_window_days,
            metric_name="churn_difficulty_pct",
            metric_value=pct_difficulty,
            threshold_value=20.0,
            alert_message=f"⚠️ {pct_difficulty:.1f}% of churn ({ease_of_use_churn}/{total_churn}) "
                          f"attributed to 'Ease of Use' difficulty in last {time_window_days} days. "
                          f"Recommend: UX audit, docs improvement, onboarding review.",
            details={
                "churn_count_total": total_churn,
                "churn_count_difficulty": ease_of_use_churn,
                "percentage": round(pct_difficulty, 2),
                "time_window_days": time_window_days,
            }
        )
        db.add(alert)
        db.commit()
        return alert
    
    return None
```

### Lógica 2: Spike en Tasa de Churn

```python
async def check_churn_rate_spike(db: Session, baseline_days: int = 60, recent_days: int = 7):
    """
    Compara tasa de churn en periodo reciente vs baseline.
    Alerta si el spike es >50% del baseline.
    """
    baseline_start = datetime.utcnow() - timedelta(days=baseline_days + recent_days)
    baseline_end = datetime.utcnow() - timedelta(days=recent_days)
    recent_start = datetime.utcnow() - timedelta(days=recent_days)
    
    # Baseline churn rate
    baseline_signups = db.scalar(
        select(func.count(User.id))
        .where(User.created_at >= baseline_start, User.created_at <= baseline_end)
    ) or 1
    
    baseline_churns = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(ChurnSurvey.cancellation_date.cast(Date) >= baseline_start.date(),
               ChurnSurvey.cancellation_date.cast(Date) <= baseline_end.date())
    ) or 0
    
    baseline_rate = (baseline_churns / baseline_signups * 100) if baseline_signups > 0 else 0
    
    # Recent churn rate
    recent_signups = db.scalar(
        select(func.count(User.id))
        .where(User.created_at >= recent_start)
    ) or 1
    
    recent_churns = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(ChurnSurvey.cancellation_date.cast(Date) >= recent_start.date())
    ) or 0
    
    recent_rate = (recent_churns / recent_signups * 100) if recent_signups > 0 else 0
    
    # Check for spike (>50% increase)
    spike_threshold = baseline_rate * 1.5
    
    if recent_rate > spike_threshold and recent_rate > 5:  # Min 5% absolute
        alert = ChurnAlert(
            alert_type="spike_in_churn_rate",
            severity="CRITICAL",
            triggered_at=datetime.utcnow(),
            time_window_days=recent_days,
            metric_name="churn_rate_pct",
            metric_value=recent_rate,
            threshold_value=spike_threshold,
            alert_message=f"🚨 CRITICAL: Churn rate spiked to {recent_rate:.1f}% "
                          f"(baseline: {baseline_rate:.1f}%, +{((recent_rate/baseline_rate - 1)*100):.0f}%) "
                          f"in last {recent_days} days. Investigate immediately.",
            details={
                "baseline_rate": round(baseline_rate, 2),
                "recent_rate": round(recent_rate, 2),
                "spike_increase_pct": round((recent_rate / baseline_rate - 1) * 100, 1),
                "baseline_period_days": baseline_days,
                "recent_period_days": recent_days,
            }
        )
        db.add(alert)
        db.commit()
        return alert
    
    return None
```

### Lógica 3: Baja Engagement = Churn Risk

```python
async def check_low_engagement_churn_pattern(db: Session, time_window_days: int = 30):
    """
    Detecta si usuarios con bajo engagement (approval_rate < 50%, active_days < 7)
    tienen tasa de churn anormalmente alta.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
    
    # Low engagement users que churnearon
    low_engagement_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .join(ChurnTelemetrySnapshot, ChurnSurvey.user_id == ChurnTelemetrySnapshot.user_id)
        .where(
            ChurnSurvey.cancellation_date >= cutoff_date.date(),
            ChurnTelemetrySnapshot.approval_rate < 0.5,
            ChurnTelemetrySnapshot.active_days_before_cancel < 7
        )
    ) or 0
    
    total_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(ChurnSurvey.cancellation_date >= cutoff_date.date())
    ) or 0
    
    if total_churn == 0:
        return None
    
    pct_low_engagement = (low_engagement_churn / total_churn * 100)
    
    if pct_low_engagement > 40:
        alert = ChurnAlert(
            alert_type="low_engagement_churn",
            severity="MEDIUM",
            triggered_at=datetime.utcnow(),
            time_window_days=time_window_days,
            metric_name="low_engagement_churn_pct",
            metric_value=pct_low_engagement,
            threshold_value=40.0,
            alert_message=f"⚠️ {pct_low_engagement:.1f}% of recent churn ({low_engagement_churn}/{total_churn}) "
                          f"comes from low-engagement users (<50% approval, <7 active days). "
                          f"Focus: better onboarding, quick wins, engagement hooks.",
            details={
                "low_engagement_churn_count": low_engagement_churn,
                "total_churn_count": total_churn,
                "percentage": round(pct_low_engagement, 2),
            }
        )
        db.add(alert)
        db.commit()
        return alert
    
    return None
```

---

## 5. Endpoints: Captura de Encuesta de Desuscripción

```python
# backend/app/main.py

@app.post("/api/churn/survey")
async def submit_churn_survey(
    user_id: UUID,
    payload: ChurnSurveyPayload,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Endpoint para que usuarios cancelen y proporcionen feedback.
    
    Flow:
    1. Captura razón principal, razones secundarias, satisfaction
    2. Captura feedback de feature request o price sensitivity
    3. Genera snapshot de telemetría de uso
    4. Dispara alertas si necesario
    5. Retorna confirmación de cancelación
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create churn survey
    survey = ChurnSurvey(
        user_id=user_id,
        primary_reason=payload.primary_reason.value,
        secondary_reasons=payload.secondary_reasons,
        satisfaction_score=payload.satisfaction_score,
        free_text_feedback=payload.free_text_feedback,
        would_return_if_feature=payload.would_return_if_feature,
        would_return_if_price_reduction=payload.would_return_if_price_reduction,
        reduction_amount_percent=payload.reduction_amount_percent,
        cancellation_date=datetime.utcnow().date(),
        survey_completed_at=datetime.utcnow(),
    )
    db.add(survey)
    db.flush()
    
    # Capture telemetry snapshot
    connection = db.scalar(select(GoogleConnection).where(GoogleConnection.user_id == user_id))
    
    # Calculate engagement metrics
    reviews = db.scalars(
        select(Review)
        .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
        .where(GoogleConnection.user_id == user_id)
    ).all()
    
    total_reviews = len(reviews)
    ai_responses_generated = sum(1 for r in reviews if r.reply_action == "AUTO_REPLY")
    ai_responses_approved = sum(1 for r in reviews if r.reply_approved_text is not None)
    approval_rate = ai_responses_approved / ai_responses_generated if ai_responses_generated > 0 else 0.0
    
    # Active days calculation
    if reviews:
        earliest_review = min(r.created_at for r in reviews)
        latest_review = max(r.created_at for r in reviews)
        active_days = (latest_review - earliest_review).days
        last_activity_days_ago = (datetime.utcnow() - latest_review).days
    else:
        active_days = 0
        last_activity_days_ago = (datetime.utcnow() - user.created_at).days
    
    telemetry = ChurnTelemetrySnapshot(
        user_id=user_id,
        churn_survey_id=survey.id,
        active_days_before_cancel=active_days,
        last_activity_days_ago=last_activity_days_ago,
        total_reviews_processed=total_reviews,
        total_ai_responses_generated=ai_responses_generated,
        total_ai_responses_approved=ai_responses_approved,
        approval_rate=approval_rate,
        used_tone_selector=connection.preferred_tone != "cercano" if connection else False,
        used_sentiment_reports=False,  # TODO: track from reports table
        used_manual_approval=ai_responses_approved > 0,
        locations_connected=1 if connection else 0,
        days_subscribed=(datetime.utcnow() - user.created_at).days,
        subscription_plan="starter",  # TODO: get from billing
    )
    db.add(telemetry)
    
    # Log lifecycle event
    event = LifecycleEvent(
        user_id=user_id,
        event_type="churn_initiated",
        metadata={
            "reason": payload.primary_reason.value,
            "satisfaction": payload.satisfaction_score,
        }
    )
    db.add(event)
    db.commit()
    
    # Trigger alert checks
    await check_ease_of_use_churn_spike(db=db, time_window_days=30)
    await check_churn_rate_spike(db=db)
    await check_low_engagement_churn_pattern(db=db)
    
    return {
        "status": "churn_recorded",
        "user_id": str(user_id),
        "survey_id": str(survey.id),
        "cancellation_effective": "immediate",
    }


@app.get("/api/churn/analytics")
def get_churn_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Dashboard de análisis de churn para product team."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total churn
    total_churn = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(ChurnSurvey.cancellation_date >= cutoff_date.date())
    ) or 0
    
    # Churn by reason (with breakout for alert threshold)
    churn_by_reason = db.execute(
        select(
            ChurnSurvey.primary_reason,
            func.count(ChurnSurvey.id).label("count"),
            func.round(100.0 * func.count(ChurnSurvey.id) / total_churn, 1).label("pct")
        )
        .where(ChurnSurvey.cancellation_date >= cutoff_date.date())
        .group_by(ChurnSurvey.primary_reason)
        .order_by("count", descending=True)
    ).all()
    
    # Average satisfaction by reason
    satisfaction_by_reason = db.execute(
        select(
            ChurnSurvey.primary_reason,
            func.round(func.avg(ChurnSurvey.satisfaction_score), 2).label("avg_score"),
            func.count(ChurnSurvey.id).label("respondents")
        )
        .where(ChurnSurvey.cancellation_date >= cutoff_date.date())
        .group_by(ChurnSurvey.primary_reason)
    ).all()
    
    # Price sensitivity: % who would stay with discount
    price_sensitive = db.scalar(
        select(func.count(ChurnSurvey.id))
        .where(
            ChurnSurvey.cancellation_date >= cutoff_date.date(),
            ChurnSurvey.would_return_if_price_reduction == True
        )
    ) or 0
    
    # Recent alerts
    recent_alerts = db.scalars(
        select(ChurnAlert)
        .where(ChurnAlert.triggered_at >= cutoff_date)
        .order_by(ChurnAlert.triggered_at.desc())
        .limit(10)
    ).all()
    
    return {
        "period_days": days,
        "total_churn": total_churn,
        "churn_by_reason": [
            {
                "reason": row.primary_reason,
                "count": row.count,
                "pct": float(row.pct),
                "alert_threshold_exceeded": float(row.pct) > 20 if row.primary_reason == "ease_of_use_difficulty" else False,
            }
            for row in churn_by_reason
        ],
        "satisfaction_by_reason": [
            {
                "reason": row.primary_reason,
                "avg_score": float(row.avg_score) if row.avg_score else None,
                "respondents": row.respondents,
            }
            for row in satisfaction_by_reason
        ],
        "price_sensitivity": {
            "count_would_return": price_sensitive,
            "pct_of_churn": round(100 * price_sensitive / total_churn, 1) if total_churn > 0 else 0,
        },
        "recent_alerts": [
            {
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.alert_message,
                "triggered_at": alert.triggered_at.isoformat(),
                "acknowledged": alert.acknowledged_at is not None,
            }
            for alert in recent_alerts
        ],
    }
```

---

## 6. Tabla de Modelos SQLAlchemy

```python
# backend/app/models.py

class LifecycleEvent(Base):
    __tablename__ = "user_lifecycle_events"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(50))
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ChurnSurvey(Base):
    __tablename__ = "churn_surveys"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    primary_reason: Mapped[str] = mapped_column(String(100))
    secondary_reasons: Mapped[list[str]] = mapped_column(ARRAY(String(100)), default=[])
    satisfaction_score: Mapped[int] = mapped_column(Integer, nullable=True)
    free_text_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    would_return_if_feature: Mapped[str] = mapped_column(String(255), nullable=True)
    would_return_if_price_reduction: Mapped[bool] = mapped_column(Boolean, default=False)
    reduction_amount_percent: Mapped[int] = mapped_column(Integer, nullable=True)
    cancellation_date: Mapped[date] = mapped_column(Date)
    survey_completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ChurnTelemetrySnapshot(Base):
    __tablename__ = "churn_telemetry_snapshot"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    churn_survey_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("churn_surveys.id", ondelete="CASCADE"), nullable=True)
    active_days_before_cancel: Mapped[int]
    last_activity_days_ago: Mapped[int]
    total_reviews_processed: Mapped[int]
    total_ai_responses_generated: Mapped[int]
    total_ai_responses_approved: Mapped[int]
    approval_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    used_tone_selector: Mapped[bool] = mapped_column(Boolean, default=False)
    used_sentiment_reports: Mapped[bool] = mapped_column(Boolean, default=False)
    used_manual_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    locations_connected: Mapped[int]
    days_subscribed: Mapped[int]
    subscription_plan: Mapped[str] = mapped_column(String(50), default="starter")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ChurnAlert(Base):
    __tablename__ = "churn_alerts"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    time_window_days: Mapped[int]
    metric_name: Mapped[str] = mapped_column(String(100), nullable=True)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    alert_message: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str] = mapped_column(String(255), nullable=True)
    resolution_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
```

---

## 7. Alembic Migration

```python
# backend/alembic/versions/20260418_0007_add_churn_tracking.py

"""add churn tracking tables and lifecycle events

Revision ID: 20260418_0007
Revises: 20260418_0006
Create Date: 2026-04-18 08:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON

revision = "20260418_0007"
down_revision = "20260418_0006"

def upgrade():
    # user_lifecycle_events
    op.create_table(
        "user_lifecycle_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("metadata", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_lifecycle_user_date", "user_lifecycle_events", ["user_id", "event_date"])
    op.create_index("idx_lifecycle_type", "user_lifecycle_events", ["event_type"])
    
    # churn_surveys
    op.create_table(
        "churn_surveys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("primary_reason", sa.String(100), nullable=False),
        sa.Column("secondary_reasons", ARRAY(sa.String(100)), server_default="{}"),
        sa.Column("satisfaction_score", sa.Integer),
        sa.Column("free_text_feedback", sa.Text),
        sa.Column("would_return_if_feature", sa.String(255)),
        sa.Column("would_return_if_price_reduction", sa.Boolean, server_default="false"),
        sa.Column("reduction_amount_percent", sa.Integer),
        sa.Column("cancellation_date", sa.Date, nullable=False),
        sa.Column("survey_completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_churn_survey_reason", "churn_surveys", ["primary_reason"])
    op.create_index("idx_churn_survey_date", "churn_surveys", ["cancellation_date"])
    
    # churn_telemetry_snapshot
    op.create_table(
        "churn_telemetry_snapshot",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("churn_survey_id", UUID(as_uuid=True), sa.ForeignKey("churn_surveys.id", ondelete="CASCADE")),
        sa.Column("active_days_before_cancel", sa.Integer, nullable=False),
        sa.Column("last_activity_days_ago", sa.Integer, nullable=False),
        sa.Column("total_reviews_processed", sa.Integer, nullable=False),
        sa.Column("total_ai_responses_generated", sa.Integer, nullable=False),
        sa.Column("total_ai_responses_approved", sa.Integer, nullable=False),
        sa.Column("approval_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("used_tone_selector", sa.Boolean, server_default="false"),
        sa.Column("used_sentiment_reports", sa.Boolean, server_default="false"),
        sa.Column("used_manual_approval", sa.Boolean, server_default="false"),
        sa.Column("locations_connected", sa.Integer, nullable=False),
        sa.Column("days_subscribed", sa.Integer, nullable=False),
        sa.Column("subscription_plan", sa.String(50), server_default="starter"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_telemetry_user", "churn_telemetry_snapshot", ["user_id"])
    op.create_index("idx_telemetry_survey", "churn_telemetry_snapshot", ["churn_survey_id"])
    
    # churn_alerts
    op.create_table(
        "churn_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("time_window_days", sa.Integer, nullable=False),
        sa.Column("metric_name", sa.String(100)),
        sa.Column("metric_value", sa.Numeric(10, 2)),
        sa.Column("threshold_value", sa.Numeric(10, 2)),
        sa.Column("alert_message", sa.Text, nullable=False),
        sa.Column("details", JSON),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_by", sa.String(255)),
        sa.Column("resolution_notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_alerts_type", "churn_alerts", ["alert_type"])
    op.create_index("idx_alerts_severity", "churn_alerts", ["severity"])
    op.create_index("idx_alerts_triggered", "churn_alerts", ["triggered_at"], postgresql_using="DESC")
    op.create_index("idx_alerts_unacknowledged", "churn_alerts", ["acknowledged_at"], postgresql_where=sa.text("acknowledged_at IS NULL"))

def downgrade():
    op.drop_table("churn_alerts")
    op.drop_table("churn_telemetry_snapshot")
    op.drop_table("churn_surveys")
    op.drop_table("user_lifecycle_events")
```

---

## 8. Dashboard de Alertas (HTML)

**Endpoint**: `GET /starter/churn-dashboard?team_token=`

Muestra:
- ⚠️ Alert badges (HIGH/CRITICAL en rojo)
- Tabla de churn reasons con % y threshold indicator
- Gráfico de tendencia de churn rate
- Tabla de usuarios de alto riesgo (prediction model future)
- Feedback directo de usuarios (quotes)
- Recomendaciones accionables

---

## 9. Tabla Resumen: Métricas Clave

| Métrica | Descripción | Alertar Si |
|---------|-------------|-----------|
| **Churn Rate** | % de usuarios activos que cancelen | >5% en 7 días |
| **Ease of Use %** | % de churn atribuido a dificultad | >20% |
| **Price Sensitivity %** | % que aceptarían volver con descuento | >30% |
| **Approval Rate (Churners)** | Approval % promedio usuarios que se van | <50% |
| **Active Days (Churners)** | Promedio días activos antes de cancelar | <7 días |
| **Satisfaction Score** | NPS-like score de encuesta | <3/5 |

---

## 10. Reporte Automático para Equipo de Producto

**Ejecutarse diariamente** (APScheduler):

```python
async def daily_churn_report(db: Session):
    """Envía reporte diario de churn a product@ via email."""
    
    alerts = db.scalars(
        select(ChurnAlert)
        .where(ChurnAlert.triggered_at >= datetime.utcnow() - timedelta(days=1))
        .order_by(ChurnAlert.severity.desc())
    ).all()
    
    if alerts:
        email_body = f"""
        === Daily Churn Alert Report ===
        
        {len(alerts)} alert(s) triggered in last 24 hours:
        
        """ + "\n".join(f"• [{a.severity}] {a.alert_type}: {a.alert_message}" for a in alerts)
        
        # Send to product team
        await send_email(
            to="product@lokigi.com",
            subject="🚨 Churn Alert Report",
            body=email_body,
        )
```

---

## Summary

**Este sistema captura**:
✅ Razón de desuscripción (9 opciones)  
✅ Feedback cuantitativo (satisfaction score, price sensitivity)  
✅ Engagement snapshot (approval rate, active days, feature adoption)  
✅ Correlación churn ↔ uso  
✅ **Alertas automáticas** cuando >20% de churn es por "Dificultad de uso"  
✅ Dashboard para product team con recomendaciones  

**Accionable para el equipo**:
- Si alerta → UX audit inmediata
- Si price sensitivity alta → pricing review
- Si low engagement → onboarding improvement
- Si switching competitor → product roadmap alignment
