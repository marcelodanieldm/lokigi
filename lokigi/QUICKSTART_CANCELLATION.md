# Quick Start: Cancellation Flow Implementation

**Tiempo total**: ~2 horas para developer experimentado

---

## 🎯 Objetivo

El usuario ve:
1. "¿Estás seguro? Has ahorrado **[X] horas este mes**" (Impact Modal)
2. Si elige "Precio" → Oferta Plan Pausa $5/mes
3. Si confirma baja → Google API permisos activos 30 días más

---

## 📝 Checklist de Implementación

### ✅ Backend Setup (30 min)

```bash
# 1. Copiar archivos backend
cp backend/app/cancellation_service.py backend/app/
cp backend/app/google_api_maintenance.py backend/app/
mkdir -p backend/app/routes
cp backend/app/routes/cancellation_routes.py backend/app/routes/
cp backend/app/routes/grace_period_routes.py backend/app/routes/

# 2. Registrar rutas en main.py
# Agregar después de otros imports:
from app.routes import cancellation_routes, grace_period_routes

# Agregar en lifespan/app.include_router:
app.include_router(cancellation_routes.router)
app.include_router(grace_period_routes.router)

# 3. Crear Alembic migration
cat > backend/alembic/versions/0008_google_grace_period.py << 'EOF'
"""Add Google API grace period tracking."""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('google_connections', 
        sa.Column('token_expiry', sa.DateTime(), nullable=True))
    op.add_column('google_connections',
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('google_connections',
        sa.Column('cancellation_metadata', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('google_connections', 'cancellation_metadata')
    op.drop_column('google_connections', 'is_revoked')
    op.drop_column('google_connections', 'token_expiry')
EOF

# 4. Ejecutar migration
cd backend
alembic upgrade head

# 5. Verificar tablas
python -c "from app.models import GoogleConnection; print('✅ Models loaded')"

# 6. Testear endpoints
python -m pytest backend/tests/test_cancellation.py -v  # Si exists
```

### ✅ Frontend Setup (25 min)

```bash
# 1. Crear directorios
mkdir -p frontend/src/components/cancellation
mkdir -p frontend/src/components/subscription
mkdir -p frontend/src/hooks

# 2. Copiar componentes
cp frontend/src/components/cancellation/CancellationModal.tsx
cp frontend/src/components/subscription/SubscriptionSettings.tsx
cp frontend/src/hooks/useCancellation.ts

# 3. Integrar en página de suscripción
# frontend/src/pages/dashboard/settings/subscription.tsx

import { SubscriptionSettings } from '@/components/subscription/SubscriptionSettings'

export default function SubscriptionPage() {
  return (
    <div className="p-6">
      <h1>Configuración de Suscripción</h1>
      <SubscriptionSettings /> {/* ← Aquí va todo! */}
    </div>
  )
}

# 4. Build frontend
npm run build
```

### ✅ Testing (30 min)

```bash
# 1. Test Endpoint 1: Impact Data
curl -X GET http://localhost:8000/api/cancellation/impact-data \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected response:
{
  "hours_saved_this_month": 4.2,
  "responses_approved_this_month": 85,
  "impact_message": "🎯 Has ahorrado 4.2 horas...",
  "total_reviews_processed": 1250,
  "approval_rate": 86.8
}

# 2. Test Endpoint 2: Initiate with price reason
curl -X POST "http://localhost:8000/api/cancellation/initiate?churn_reason=price_too_high" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected: Returns offers including Plan Pausa

# 3. Test Endpoint 3: Plan Pausa activation
curl -X POST http://localhost:8000/api/cancellation/plan-pausa \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"duration_days": 90}'

# Expected: status: "success", access_level: "read_only"

# 4. Test Endpoint 4: Full cancellation
curl -X POST http://localhost:8000/api/cancellation/confirm \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"churn_reason": "price_too_high", "churn_detail": "Too expensive"}'

# Expected: google_api_permissions_active_until is set

# 5. Test Frontend
- Navigate to /dashboard/settings/subscription
- Click "Cancelar Suscripción"
- Verify Impact Modal shows
- Select "Demasiado caro"
- Verify Plan Pausa offer shows
- Click "Continuar Cancelación"
- Enter feedback
- Click "Confirmar"
- Verify success message
```

---

## 🔧 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Modal no se abre | Verificar que `<CancellationModal>` importado en SubscriptionSettings |
| Impact data es 0 | Verificar que usuario tiene Google connection + reviews |
| Plan Pausa no activa | Verificar que Stripe SKU $5 está creada + token en env |
| Token_expiry NULL | Verificar que migration 0008 se ejecutó y DB actualizó |

---

## 📊 Flujo de Usuario (Una vez implementado)

```
1. Usuario en Panel → Settings → Subscription
2. Hace click "Cancelar Suscripción"
3. Ve Modal: "Has ahorrado 4.2 horas este mes" ← STEP 1
4. Lee "Antes de irte..." + impacto
5. Click "Continuar Cancelación"
6. Selecciona motivo: "Demasiado caro" ← STEP 2
7. Ve oferta: "Plan Pausa $5/mes - 90 días" ← STEP 3
8. Opción A: Click "Activar Plan Pausa" → Stripe actualiza → Success
9. Opción B: Click "Continuar Cancelación"
10. Escribe feedback (opcional) ← STEP 4
11. Click "Confirmar Cancelación"
12. Backend: Guarda survey + telemetry + google permisos por 30 días
13. Frontend: Modal cierra + Mensaje de confirmación
```

---

## 📈 Métricas a Trackear

Después de implementar, monitorea:

```
POST /api/cancellation/initiate
  → counts iniciaciones por reason
  
POST /api/cancellation/plan-pausa
  → counts conversiones a Plan Pausa
  → revenue mensual = count × $5
  
POST /api/cancellation/confirm
  → counts cancelaciones finales
  → churn rate = confirm_count / total_users
  
GET /api/cancellation/grace-period-status
  → % usuarios que reactivan durante grace period
  → reactivation_revenue = reactivate_count × $29
```

---

## ⚡ One-Liner Checks

```bash
# ¿Backend está corriendo?
curl http://localhost:8000/api/cancellation/impact-data

# ¿DB migration ejecutada?
psql -c "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='google_connections' AND column_name='token_expiry')"

# ¿Frontend compila?
npm run build

# ¿API retorna datos reales?
curl -s http://localhost:8000/api/cancellation/impact-data | jq '.hours_saved_this_month'
```

---

## 📋 Orden Recomendado de Ejecución

1. **Primero**: Alembic migration (sin esto nada funciona)
2. **Segundo**: Backend files + rutas
3. **Tercero**: Frontend components  
4. **Cuarto**: Testing manual
5. **Quinto**: Deploy a staging
6. **Sexto**: Monitor en producción

---

## 🚀 Deploy a Producción

```bash
# 1. Backend
cd backend
alembic upgrade head  # ⚠️ DO THIS FIRST
git add cancellation_service.py google_api_maintenance.py routes/
git commit -m "feat: cancellation flow with Plan Pausa"
git push

# 2. Frontend
cd frontend
git add components/cancellation/ components/subscription/ hooks/
git commit -m "feat: cancellation modal with impact data"
git push

# 3. Monitor
- Watch churn_rate metric
- Alert si Plan Pausa activation < 10%
- Alert si grace_period cleanup fails
```

---

## 📞 Si Algo Falla

Revisar en este orden:

1. **Backend no bootea**: Check syntax `python -m py_compile`
2. **Endpoints 404**: Check router inclusion en main.py
3. **Modal blank**: Check browser console para JS errors
4. **No datos en Impact**: Verify user tiene Google connections + reviews
5. **Stripe error**: Check API key en .env
6. **DB error**: Verify migration ejecutada: `alembic current`

---

## 💡 Pro Tips

- Si quieres testear sin usuario real: Create mock user + reviews en DB
- Plan Pausa se puede testear con Stripe test mode
- Grace period cleanup se puede triggerar manualmente: `python scripts/trigger_cleanup.py`
- Monitor logs para errors: `tail -f logs/api.log | grep cancellation`

---

**¿Listo para comenzar?** Empieza por el Checklist Backend Step 1 → Done en 2 horas ✅

