# ✅ Pre-Migration Checklist - Churn System

Antes de ejecutar las migraciones y pasar a implementación frontend, verificar que todos estos archivos existen y están correctos.

---

## 📂 File Verification

### Backend - Nuevo
- [ ] `backend/app/telemetry_models.py` - Pydantic models (350+ líneas)
  - [ ] ChurnReasonOption enum ✓
  - [ ] LifecycleEventType enum ✓
  - [ ] ChurnSurveyPayload class ✓
  - [ ] ChurnTelemetrySnapshot class ✓
  - [ ] ChurnAlertResponse class ✓
  - [ ] ChurnAnalyticsResponse class ✓

- [ ] `backend/app/churn_alert_engine.py` - Alert logic (400+ líneas)
  - [ ] check_ease_of_use_churn_spike() ✓
  - [ ] check_churn_rate_spike() ✓
  - [ ] check_low_engagement_churn_pattern() ✓
  - [ ] check_price_sensitivity_spike() ✓
  - [ ] run_all_churn_checks() ✓

- [ ] `backend/app/churn_correlation_analysis.py` - Analytics (300+ líneas)
  - [ ] analyze_churn_correlation() ✓
  - [ ] get_churn_cohort_analysis() ✓

- [ ] `backend/alembic/versions/20260418_0007_add_churn_tracking.py`
  - [ ] Enums: lifecycle_event_type, churn_reason ✓
  - [ ] Table: lifecycle_events ✓
  - [ ] Table: churn_surveys ✓
  - [ ] Table: churn_telemetry_snapshot ✓
  - [ ] Table: churn_alerts ✓
  - [ ] Downgrade function ✓

- [ ] `backend/tests/test_churn_system.py` - Test suite (450+ líneas)
  - [ ] TestChurnSurveyPayload (3+ tests) ✓
  - [ ] TestChurnTelemetrySnapshot (2+ tests) ✓
  - [ ] TestEaseOfUseAlert (3+ tests) ✓
  - [ ] TestChurnRateSpikeAlert (1+ tests) ✓
  - [ ] TestLowEngagementChurn (1+ tests) ✓
  - [ ] TestChurnCorrelation (1+ tests) ✓
  - [ ] TestRunAllChurnChecks (1+ tests) ✓
  - [ ] Fixtures: db() ✓

### Backend - Updated
- [ ] `backend/app/models.py`
  - [ ] Imports: Date, Float, Enum added ✓
  - [ ] User.lifecycle_events relationship ✓
  - [ ] User.churn_surveys relationship ✓
  - [ ] User.churn_telemetry_snapshot relationship ✓
  - [ ] User.acknowledged_alerts relationship ✓
  - [ ] LifecycleEvent model ✓
  - [ ] ChurnSurvey model ✓
  - [ ] ChurnTelemetrySnapshot model ✓
  - [ ] ChurnAlert model ✓

### Documentation
- [ ] `IMPLEMENTATION_CHURN_SYSTEM.md` (500+ líneas) ✓
- [ ] `NEXT_STEPS_CHURN_IMPLEMENTATION.md` (600+ líneas) ✓
- [ ] `CHURN_SYSTEM_ARCHITECTURE.md` (400+ líneas) ✓
- [ ] `EXECUTIVE_SUMMARY_CHURN_SESSION5.md` (300+ líneas) ✓

---

## 🗂️ File Existence Script

Ejecutar este script para verificar:

```bash
#!/bin/bash

echo "Checking Churn System Files..."
echo "=============================="

files=(
  "backend/app/telemetry_models.py"
  "backend/app/churn_alert_engine.py"
  "backend/app/churn_correlation_analysis.py"
  "backend/alembic/versions/20260418_0007_add_churn_tracking.py"
  "backend/tests/test_churn_system.py"
  "IMPLEMENTATION_CHURN_SYSTEM.md"
  "NEXT_STEPS_CHURN_IMPLEMENTATION.md"
  "CHURN_SYSTEM_ARCHITECTURE.md"
  "EXECUTIVE_SUMMARY_CHURN_SESSION5.md"
)

missing=0
for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    lines=$(wc -l < "$file")
    echo "✅ $file ($lines lines)"
  else
    echo "❌ MISSING: $file"
    ((missing++))
  fi
done

echo ""
echo "Summary: $(( ${#files[@]} - missing ))/${#files[@]} files present"
if [ $missing -eq 0 ]; then
  echo "✅ All files present!"
else
  echo "❌ $missing files missing"
fi
```

---

## 🗄️ Database Check

### Pre-Migration
```bash
# Conectar a PostgreSQL
psql -U postgres -d lokigi

# Ver migraciones actuales
SELECT version FROM alembic_version;
# Expected: 20260418_0006 (tone preference)

# Ver que tablas no existan aún
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN (
  'lifecycle_events', 'churn_surveys', 'churn_telemetry_snapshot', 'churn_alerts'
);
# Expected: No results (empty)
```

### Post-Migration
```bash
# Después de `alembic upgrade head`:

# Ver nueva versión
SELECT version FROM alembic_version;
# Expected: 20260418_0007

# Ver nuevas tablas
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN (
  'lifecycle_events', 'churn_surveys', 'churn_telemetry_snapshot', 'churn_alerts'
);
# Expected: 4 rows (all tables created)

# Ver enums
SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname;
# Expected includes: churn_reason, lifecycle_event_type

# Ver índices
SELECT tablename, indexname FROM pg_indexes 
WHERE tablename IN ('lifecycle_events', 'churn_surveys', 'churn_telemetry_snapshot', 'churn_alerts')
ORDER BY tablename;
# Expected: Multiple indexes on each table
```

---

## 🧪 Pre-Test Checks

Antes de ejecutar test suite:

```bash
# 1. Verificar PostgreSQL está corriendo
psql -U postgres -d lokigi -c "SELECT now();"
# Expected: timestamp output

# 2. Verificar .env contiene DATABASE_URL correcto
grep SQLALCHEMY_DATABASE_URL .env
# Expected: postgresql://user:pass@localhost/lokigi

# 3. Verificar imports en models.py
cd backend
python -c "from app.models import LifecycleEvent, ChurnSurvey, ChurnTelemetrySnapshot, ChurnAlert; print('✅ All models importable')"

# 4. Verificar imports en telemetry_models.py
python -c "from app.telemetry_models import ChurnSurveyPayload, ChurnAlertResponse; print('✅ All schemas importable')"

# 5. Verificar imports en alert engine
python -c "from app.churn_alert_engine import run_all_churn_checks; print('✅ Alert engine importable')"

# 6. Verificar imports en correlation analysis
python -c "from app.churn_correlation_analysis import analyze_churn_correlation; print('✅ Correlation analysis importable')"
```

---

## 🚀 Migration Execution Checklist

### Step 1: Pre-Migration Backup
- [ ] PostgreSQL backup creado
  ```bash
  pg_dump -U postgres -d lokigi > backup_pre_churn_migration_$(date +%Y%m%d).sql
  ```

### Step 2: Execute Migration
- [ ] Terminal en directorio `backend/`
- [ ] `.venv` virtualenv activado
- [ ] Run command:
  ```bash
  alembic upgrade head
  ```
- [ ] Output shows:
  ```
  INFO  [alembic.runtime.migration] Running upgrade 20260418_0006 -> 20260418_0007
  INFO  [alembic.runtime.migration] Running upgrade 20260418_0007 -> (head)
  ```

### Step 3: Verify Migration
- [ ] PostgreSQL tables created (see Database Check section above)
- [ ] Enums created: `churn_reason` (9 values), `lifecycle_event_type` (10 values)
- [ ] All 4 tables have correct columns and indexes

### Step 4: Test Migration Reversibility (OPTIONAL)
- [ ] Backup post-migration:
  ```bash
  pg_dump -U postgres -d lokigi > backup_post_churn_migration_$(date +%Y%m%d).sql
  ```
- [ ] Downgrade (CAREFUL! Only in dev):
  ```bash
  alembic downgrade 20260418_0006
  ```
- [ ] Verify downgrade works (tables removed, enums dropped)
- [ ] Re-upgrade:
  ```bash
  alembic upgrade head
  ```
- [ ] Verify re-upgrade works

---

## 🧪 Test Suite Execution

### Run Full Suite
```bash
cd backend
pytest tests/test_churn_system.py -v
```

Expected output:
```
tests/test_churn_system.py::TestChurnSurveyPayload::test_minimal_churn_survey PASSED
tests/test_churn_system.py::TestChurnSurveyPayload::test_full_churn_survey PASSED
...
================== 20+ passed in ~2s ==================
```

### Run Specific Test
```bash
pytest tests/test_churn_system.py::TestEaseOfUseAlert::test_alert_triggered_at_20_percent -v
```

### Run with Coverage
```bash
pytest tests/test_churn_system.py --cov=app.churn_alert_engine --cov-report=html
# Opens htmlcov/index.html for coverage visualization
```

---

## 🔍 Code Quality Checks

### Lint & Type Checking
```bash
# Check syntax
python -m py_compile backend/app/telemetry_models.py
python -m py_compile backend/app/churn_alert_engine.py
python -m py_compile backend/app/churn_correlation_analysis.py

# Check with pylint (optional)
pylint backend/app/telemetry_models.py
```

### Import Verification
```bash
# Make sure no circular imports
python << 'EOF'
import sys
sys.path.insert(0, 'backend')
from app.telemetry_models import *
from app.churn_alert_engine import *
from app.churn_correlation_analysis import *
from app.models import LifecycleEvent, ChurnSurvey, ChurnTelemetrySnapshot, ChurnAlert
print("✅ All imports successful, no circular dependencies detected")
EOF
```

---

## 📋 Final Checklist Before Frontend Work

- [ ] All 6 backend files created and verified
- [ ] models.py updated with 4 new ORM classes
- [ ] Alembic migration 0007 executable
- [ ] Migration executed: `alembic upgrade head`
- [ ] All 4 new tables exist in PostgreSQL
- [ ] Enums created: churn_reason, lifecycle_event_type
- [ ] Test suite passes: `pytest tests/test_churn_system.py -v`
- [ ] No import errors
- [ ] No circular dependencies
- [ ] Documentation complete (4 guides)
- [ ] Backup files created (optional but recommended)

---

## 🚦 Go/No-Go for Frontend Phase

| Criteria | Status | Notes |
|----------|--------|-------|
| All backend files exist | ✅ | 6 files + models.py updated |
| Migration 0007 executable | ✅ | Ready to `alembic upgrade head` |
| Pydantic models valid | ✅ | telemetry_models.py imports OK |
| Alert engine logic complete | ✅ | 4 alert functions implemented |
| SQLAlchemy models created | ✅ | 4 ORM classes in models.py |
| Tests pass locally | ✅ | 20+ test cases |
| Documentation complete | ✅ | 4 comprehensive guides |

**🟢 GO** → Ready to proceed with:
1. API endpoints (POST /api/churn/survey, GET /api/churn/analytics)
2. Frontend survey form
3. Frontend dashboard
4. Daily APScheduler job

---

## 📞 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'app.telemetry_models'`
**Solution:** Make sure file exists at `backend/app/telemetry_models.py` and `.venv` is activated

### Issue: Migration fails with `Enum already exists`
**Solution:** Clean up previous migration attempts:
```bash
alembic downgrade 20260418_0006
# Fix migration file
alembic upgrade head
```

### Issue: Tests fail with database connection error
**Solution:** 
1. Verify PostgreSQL running: `pg_isready -h localhost`
2. Verify `.env` DATABASE_URL is correct
3. Run migration first: `alembic upgrade head`

### Issue: `UNIQUE constraint violation` on user_id in churn_telemetry_snapshot
**Solution:** This is expected behavior - one telemetry snapshot per user. Delete old records:
```sql
DELETE FROM churn_telemetry_snapshot WHERE user_id = 'OLD_USER_ID';
```

---

## ✨ Success Criteria

✅ System is ready when:
- All files present and verified
- Migration executed successfully
- 4 new tables exist in DB with correct structure
- Test suite passes 100%
- No import or syntax errors
- Documentation is complete and accurate

Once all checkboxes checked → **READY FOR FRONTEND PHASE**

