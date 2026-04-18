# 🚀 Pasos Siguientes - Churn System Implementation

Este documento proporciona instrucciones claras para completar la implementación del sistema de churn.

---

## ✅ Completado Esta Sesión

- ✅ Modelos Pydantic (telemetry_models.py)
- ✅ Motor de alertas (churn_alert_engine.py)
- ✅ Análisis correlacional (churn_correlation_analysis.py)
- ✅ Migración Alembic 0007 (lista para ejecutar)
- ✅ Modelos SQLAlchemy (models.py actualizado)
- ✅ Suite de tests (test_churn_system.py)
- ✅ Documentación completa

---

## 📋 PASO 1: Ejecutar Migración Alembic

### Prerequisitos
- PostgreSQL corriendo
- Backend `.venv` activado
- Estar en directorio `backend/`

### Comando
```bash
cd backend
alembic upgrade head
```

### Resultado Esperado
```
INFO  [alembic.runtime.migration] Context impl PostgreSQLImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 20260418_0006 -> 20260418_0007, add lifecycle and churn tracking tables

  Running alembic upgrade ... [OK]
```

### Verificar en PostgreSQL
```sql
-- Conectarse a la BD
psql -U postgres -d lokigi

-- Ver tablas nuevas
\dt lifecycle_events churn_surveys churn_telemetry_snapshot churn_alerts

-- Ver enums
SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname;
-- Debería mostrar: churn_reason, lifecycle_event_type
```

---

## 📋 PASO 2: Ejecutar Test Suite

### Comando
```bash
cd backend
pytest tests/test_churn_system.py -v
```

### Resultado Esperado
```
tests/test_churn_system.py::TestChurnSurveyPayload::test_minimal_churn_survey PASSED
tests/test_churn_system.py::TestChurnSurveyPayload::test_full_churn_survey PASSED
tests/test_churn_system.py::TestChurnSurveyPayload::test_invalid_satisfaction_score PASSED
...
================== 20 passed in 2.34s ==================
```

### Troubleshooting
Si fallan tests:
1. Asegurar `alembic upgrade head` ejecutado
2. Revisar que `SQLALCHEMY_DATABASE_URL` en `.env` es correcto
3. Confirmr que PostgreSQL está accesible

---

## 🔌 PASO 3: Crear Endpoints API (backend/app/main.py)

### Importar nuevos modelos
En la parte superior de `main.py`:
```python
from app.telemetry_models import (
    ChurnSurveyPayload,
    ChurnAnalyticsResponse,
)
from app.churn_alert_engine import run_all_churn_checks
from app.churn_correlation_analysis import analyze_churn_correlation
```

### Endpoint 1: POST /api/churn/survey

Insertar después de los otros endpoints `/api/`:

```python
@app.post("/api/churn/survey")
async def submit_churn_survey(
    payload: ChurnSurveyPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    User submits churn feedback when canceling subscription.
    
    Flow:
    1. Guardar ChurnSurvey con feedback cualitativo
    2. Capturar ChurnTelemetrySnapshot con métricas en ese momento
    3. Ejecutar todos los alert checks
    4. Retornar alerts triggered (si hay)
    """
    from app.models import ChurnSurvey, ChurnTelemetrySnapshot as TelemetryModel
    from sqlalchemy import func, select
    
    try:
        # 1. Guardar survey
        today = datetime.utcnow().date()
        survey = ChurnSurvey(
            user_id=user.id,
            cancellation_date=today,
            primary_reason=payload.primary_reason.value,
            secondary_reasons=[r.value for r in payload.secondary_reasons] if payload.secondary_reasons else [],
            satisfaction_score=payload.satisfaction_score,
            free_text_feedback=payload.free_text_feedback,
            would_return_if_feature=payload.would_return_if_feature,
            would_return_if_price_reduction=payload.would_return_if_price_reduction,
            reduction_amount_percent=payload.reduction_amount_percent,
        )
        db.add(survey)
        db.commit()
        
        # 2. Capturar snapshot de engagement
        # Contar reviews, responses, approval rate del user
        reviews_count = db.scalar(
            select(func.count(Review.id))
            .join(GoogleConnection)
            .where(GoogleConnection.user_id == user.id)
        ) or 0
        
        approved_count = db.scalar(
            select(func.count(Review.id))
            .join(GoogleConnection)
            .where(
                GoogleConnection.user_id == user.id,
                Review.reply_sent_at.isnot(None),
            )
        ) or 0
        
        approval_rate = (approved_count / reviews_count) if reviews_count > 0 else 0.0
        
        # Contar días activos (desde signup hasta ahora)
        active_days = (datetime.utcnow().date() - user.created_at.date()).days
        
        # Verificar si usó tone selector (existe preferred_tone != default)
        connection = db.query(GoogleConnection).filter_by(user_id=user.id).first()
        used_tone = connection and connection.preferred_tone != "cercano"
        
        # Crear snapshot (borrar anterior si existe)
        db.query(TelemetryModel).filter_by(user_id=user.id).delete()
        
        telemetry = TelemetryModel(
            user_id=user.id,
            active_days_before_cancel=active_days,
            last_activity_days_ago=3,  # TODO: Calcular real desde last Review
            total_reviews_processed=reviews_count,
            total_ai_responses_generated=approved_count,  # Simplified; count actual generated
            total_ai_responses_approved=approved_count,
            approval_rate=approval_rate,
            used_tone_selector=used_tone,
            used_sentiment_reports=False,  # TODO: Track if used sentiment report
            used_manual_approval=True,  # All reviews require manual approval
            locations_connected=1,  # TODO: Count actual
            days_subscribed=active_days,
            subscription_plan="starter",
        )
        db.add(telemetry)
        db.commit()
        
        # 3. Ejecutar alert checks
        alerts = await run_all_churn_checks(db)
        
        # 4. Retornar resultado
        return {
            "status": "success",
            "survey_id": str(survey.id),
            "alerts_triggered": len(alerts),
            "alerts": [
                {
                    "type": a.alert_type,
                    "severity": a.severity,
                    "message": a.alert_message,
                }
                for a in alerts
            ],
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

### Endpoint 2: GET /api/churn/analytics

Insertar después del endpoint anterior:

```python
@app.get("/api/churn/analytics")
async def get_churn_analytics(
    days: int = Query(30, ge=1, le=90, description="Analysis window in days"),
    user: User = Depends(get_current_user),  # TODO: Add role check for admin
    db: Session = Depends(get_db),
):
    """
    Product team dashboard: recent alerts, churn reasons, correlations.
    
    Requires: role == "admin" (TODO: implement role checking)
    """
    from app.models import ChurnAlert
    
    try:
        # 1. Recent alerts (últimos 7 días)
        alert_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_alerts = db.query(ChurnAlert)\
            .filter(ChurnAlert.triggered_at >= alert_cutoff)\
            .order_by(ChurnAlert.triggered_at.desc())\
            .limit(20)\
            .all()
        
        # 2. Correlation analysis
        correlation = await analyze_churn_correlation(db, time_window_days=days)
        
        # 3. Build response
        response = ChurnAnalyticsResponse(
            period_days=days,
            total_churn=sum(c.churn_count for c in correlation.correlations),
            churn_by_reason=[
                ChurnAnalyticsResponse.ChurnReasonBreakdown(
                    reason=c.reason,
                    count=c.churn_count,
                    pct=c.pct_of_total,
                    alert_threshold_exceeded=(
                        c.reason == "ease_of_use_difficulty" and c.pct_of_total > 20
                    ),
                )
                for c in correlation.correlations
            ],
            satisfaction_by_reason=[
                ChurnAnalyticsResponse.SatisfactionData(
                    reason=r.reason,
                    avg_score=3.0,  # TODO: Calculate actual average
                    respondents=r.churn_count,
                )
                for r in correlation.correlations
            ],
            price_sensitivity=ChurnAnalyticsResponse.PriceSensitivity(
                count_would_return=0,  # TODO: Query from ChurnSurvey
                pct_of_churn=0.0,
            ),
            recent_alerts=[
                ChurnAlertResponse(
                    id=str(a.id),
                    alert_type=a.alert_type,
                    severity=a.severity,
                    message=a.alert_message,
                    triggered_at=a.triggered_at,
                    time_window_days=a.time_window_days,
                    metric_name=a.metric_name,
                    metric_value=a.metric_value,
                    threshold_value=a.threshold_value,
                    details=a.details,
                    acknowledged=a.acknowledged_at is not None,
                )
                for a in recent_alerts
            ],
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Test Endpoints con curl
```bash
# Test churn survey submission
curl -X POST http://localhost:8000/api/churn/survey \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "primary_reason": "ease_of_use_difficulty",
    "satisfaction_score": 2,
    "free_text_feedback": "Dashboard too complex"
  }'

# Test analytics dashboard
curl -X GET "http://localhost:8000/api/churn/analytics?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎨 PASO 4: Frontend - Churn Survey Form

### Crear archivo: frontend/src/pages/ChurnSurvey.tsx

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const CHURN_REASONS = [
  { value: 'price_too_high', label: '💰 Price too high' },
  { value: 'lack_of_features', label: '❌ Missing features' },
  { value: 'ease_of_use_difficulty', label: '🤔 Too complicated' },
  { value: 'switched_competitor', label: '🔄 Switched competitor' },
  { value: 'not_using_enough', label: '😴 Not using enough' },
  { value: 'poor_support', label: '📞 Poor support' },
  { value: 'technical_issues', label: '⚠️ Technical issues' },
  { value: 'personal_reasons', label: '👤 Personal reasons' },
  { value: 'other', label: '❓ Other' },
];

export default function ChurnSurvey() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    primary_reason: '',
    satisfaction_score: 3,
    free_text_feedback: '',
    would_return_if_price_reduction: false,
    reduction_amount_percent: 10,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/churn/survey', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('Failed to submit survey');

      const data = await response.json();
      
      // Show confirmation + alerts if triggered
      alert(`Survey submitted!\n\nAlerts triggered: ${data.alerts_triggered}`);
      
      // Redirect to account or home
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h1 className="text-3xl font-bold mb-2">We're sorry to see you go</h1>
      <p className="text-gray-600 mb-6">Help us improve by sharing why you're canceling:</p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Primary Reason */}
        <div>
          <label className="block text-lg font-semibold mb-3">What's the main reason?</label>
          <div className="grid grid-cols-1 gap-3">
            {CHURN_REASONS.map((reason) => (
              <label key={reason.value} className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="primary_reason"
                  value={reason.value}
                  checked={formData.primary_reason === reason.value}
                  onChange={(e) => setFormData({...formData, primary_reason: e.target.value})}
                  className="mr-3"
                  required
                />
                <span>{reason.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Satisfaction Score */}
        <div>
          <label className="block text-lg font-semibold mb-3">How satisfied were you? (1-5)</label>
          <input
            type="range"
            min="1"
            max="5"
            value={formData.satisfaction_score}
            onChange={(e) => setFormData({...formData, satisfaction_score: parseInt(e.target.value)})}
            className="w-full"
          />
          <div className="flex justify-between text-sm text-gray-500 mt-1">
            <span>Very Unsatisfied</span>
            <span className="font-bold text-lg">{formData.satisfaction_score}</span>
            <span>Very Satisfied</span>
          </div>
        </div>

        {/* Free Text Feedback */}
        <div>
          <label className="block text-lg font-semibold mb-2">Additional feedback (optional)</label>
          <textarea
            value={formData.free_text_feedback}
            onChange={(e) => setFormData({...formData, free_text_feedback: e.target.value})}
            placeholder="Tell us more..."
            className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
        </div>

        {/* Price Sensitivity */}
        <div>
          <label className="flex items-center p-3 border rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={formData.would_return_if_price_reduction}
              onChange={(e) => setFormData({...formData, would_return_if_price_reduction: e.target.checked})}
              className="mr-3"
            />
            <span className="font-semibold">Would return with price reduction?</span>
          </label>

          {formData.would_return_if_price_reduction && (
            <div className="mt-3 p-3 bg-blue-50 rounded-lg">
              <label className="block text-sm font-semibold mb-2">What discount % would persuade you?</label>
              <input
                type="number"
                min="5"
                max="50"
                value={formData.reduction_amount_percent}
                onChange={(e) => setFormData({...formData, reduction_amount_percent: parseInt(e.target.value)})}
                className="w-24 p-2 border rounded-lg"
              />
              <span className="ml-2 text-sm text-gray-600">%</span>
            </div>
          )}
        </div>

        {/* Error */}
        {error && <div className="p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !formData.primary_reason}
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? 'Submitting...' : 'Submit Feedback'}
        </button>
      </form>
    </div>
  );
}
```

---

## 📊 PASO 5: Frontend - Analytics Dashboard

### Crear archivo: frontend/src/pages/admin/ChurnAnalytics.tsx

(Similar structure con gráficos, tabla de alertas, etc.)

---

## 🔄 PASO 6: Setup Daily Alert Job

En `backend/app/monthly_report_worker.py`, agregar:

```python
async def daily_churn_report(db: Session):
    """Run churn monitoring checks daily (08:00 UTC)."""
    from app.churn_alert_engine import run_all_churn_checks
    from app.utils.email_sendgrid import send_email
    
    alerts = await run_all_churn_checks(db)
    
    critical_alerts = [a for a in alerts if a.severity in ["HIGH", "CRITICAL"]]
    
    if critical_alerts:
        email_body = "<h2>🚨 Churn Alerts Report</h2>"
        for alert in critical_alerts:
            email_body += f"""
            <div style="margin: 20px 0; padding: 15px; border-left: 4px solid red;">
                <h3>{alert.alert_type} ({alert.severity})</h3>
                <p>{alert.alert_message}</p>
                <p><small>Triggered: {alert.triggered_at.isoformat()}</small></p>
            </div>
            """
        
        email_body += f"""
        <p><a href="https://lokigi.com/admin/churn/analytics">View Full Dashboard →</a></p>
        """
        
        await send_email(
            to="product@lokigi.com",
            subject=f"🚨 {len(critical_alerts)} Churn Alerts - Action Required",
            html_body=email_body,
        )

# En la función de setup scheduler:
scheduler.add_job(
    daily_churn_report,
    trigger=CronTrigger(hour=8, minute=0),
    id="daily_churn_report",
)
```

---

## ✨ Checklist Final

- [ ] `alembic upgrade head` ejecutado exitosamente
- [ ] Test suite pasa: `pytest tests/test_churn_system.py -v`
- [ ] Endpoints POST /api/churn/survey y GET /api/churn/analytics creados
- [ ] Frontend survey form funcional
- [ ] Frontend analytics dashboard funcional
- [ ] Daily job configurado en APScheduler
- [ ] Email alerts enviados a product@lokigi.com
- [ ] Documentación actualizada en README.md

---

## 🎯 Success Criteria

✅ Sistema captura churn reasons + engagement metrics
✅ 4 tipos de alertas automáticas funcionando
✅ Product team recibe emails diarios con alertas
✅ Dashboard muestra correlaciones entre churn y engagement
✅ Usuarios pueden reportar feedback al cancelar
✅ Sistema mantiene histórico completo para análisis

