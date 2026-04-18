# Lokigi

Lokigi centraliza automatización de reseñas de Google Business Profile para el Plan Starter: onboarding guiado, generación y aprobación de respuestas, autoenvío programable, perfil operativo, suscripción/facturación, reportes mensuales, análisis de sentimiento, churn/cancelación y análisis NLP de respuestas editadas.

## Estado actual

### Plataforma base
- OAuth2 con Google Business Profile.
- Restricción de una ubicación por usuario en Starter y validación de upgrade a Growth si intentan conectar una segunda.
- Ingesta de `NEW_REVIEW` vía Pub/Sub.
- Persistencia de reseñas con protección ante colisiones por `review_id` y hash de payload.
- Tokens OAuth cifrados con Fernet.

### Motor de respuestas y operación Starter
- Motor NLP con detección de idioma y clasificación `ALERT` / `AUTO_REPLY`.
- Selector de tono `cercano`, `formal`, `moderno` con preview en tiempo real.
- Activación Starter con flags `manual_approval_enabled` y `negative_review_whatsapp_enabled`.
- Configuración de perfil Starter con palabras prohibidas y `response_schedule` (`instant` o `delay_1h`).
- Filtro de palabras prohibidas aplicado antes de mostrar o enviar respuestas.
- Autoenvío inmediato o diferido 1 hora según configuración del usuario.
- Worker `auto_reply_worker.py` ejecutado por scheduler cada minuto para despachar respuestas pendientes.

### Flujo UX de onboarding
- `/starter/onboarding` como pantalla de entrada.
- `/starter/connect-google` para iniciar OAuth con contexto Starter.
- `/starter/loading` como pantalla intermedia de inicialización.
- `/starter/tone-selector` para tono y activación final.
- `/starter/dashboard` con negocio conectado, tono, flags y últimas reseñas.

### Aprobación humana de respuestas
- `/starter/approvals` como UI server-rendered sin build frontend.
- `GET /api/reviews/pending` para pendientes.
- `POST /api/reviews/{id}/approve` para aprobar y enviar.
- `POST /api/reviews/{id}/regenerate` para regenerar sugerencia.

### Perfil, suscripción y billing
- Página de perfil Starter en `/starter/profile`.
- Página de suscripción y facturas en `/starter/subscription`.
- Modelo `SubscriptionProfile` para estado y referencias Stripe.
- APIs:
  - `GET /api/subscription/status`
  - `GET /api/subscription/invoices`
  - `GET /api/subscription/upgrade-check`
  - `POST /api/subscription/upgrade/growth`
- Upsell automático a Growth cuando Starter intenta añadir una segunda ubicación.

### Métricas mensuales, valor y sentimiento
- Tabla `StarterMonthlyMetrics` para KPIs mensuales.
- Reportes persistidos en `monthly_reports`.
- Scheduler APScheduler con job mensual de reportes y job por minuto de autoenvío.
- Reporte HTML en `/starter/report`.
- Historial de reportes en dashboard con lista cronológica mensual y acciones `Ver Online` / `Descargar PDF`.
- Endpoint de estado/URL PDF por periodo en `/api/reports/monthly-pdf`.
- Integración con worker asíncrono (`backend/pdf-worker`) para generar PDF, subir a S3 y guardar signed URL.
- Envío automático de email mensual (día 1) con CTA a reporte online y botón directo al PDF cuando está disponible.
- Análisis de sentimiento con:
  - conceptos positivos y negativos
  - conceptos top globales
  - snapshot de positivas / neutrales / negativas
  - `chart_data` listo para visualización
- Métricas de valor añadidas al reporte:
  - velocidad de respuesta actual vs baseline histórico
  - snapshot de sentimiento
  - keyword cloud

### Reporte PDF Premium (4 páginas)
- Página 1: resumen ejecutivo y métricas estrella (nota media y tiempo ahorrado).
- Página 2: análisis de sentimiento (qué aman tus clientes y qué les molesta).
- Página 3: selección de mejores interacciones (reseñas destacadas + respuesta Lokigi).
- Página 4: consejos estratégicos de Lokigi para el siguiente mes.

### Insights IA en dashboard
- Servicio `starter_tip_service.py` con fallback heurístico y opción LLM compatible OpenAI.
- Endpoint `GET /api/nlp/starter-tip-of-day` para consumo de Tip del Día.
- Tip del Día integrado en dashboard con foco, confianza, evidencia y señales de soporte.

### Cancelación, retención y churn
- Flujo de cancelación con Impact Modal y oferta `Plan Pausa`.
- Servicio `cancellation_service.py` para:
  - horas ahorradas del mes
  - inicio de cancelación con ofertas
  - activación de `Plan Pausa`
  - confirmación de cancelación
  - email de despedida con enlace a PDF de métricas
- Rutas incluidas en FastAPI:
  - `GET /api/cancellation/impact-data`
  - `POST /api/cancellation/initiate`
  - `POST /api/cancellation/plan-pausa`
  - `POST /api/cancellation/confirm`
  - `GET /api/cancellation/grace-period-status`
- Modelos de churn y lifecycle en `backend/app/models.py`.
- Alert engine y análisis correlacional en:
  - `backend/app/churn_alert_engine.py`
  - `backend/app/churn_correlation_analysis.py`
- Migración Alembic de churn en `20260418_0007_add_churn_tracking.py`.

### Análisis NLP de respuestas editadas
- Motor `backend/app/nlp_edit_analysis.py` para comparar `reply_public_text` vs `reply_approved_text`.
- Detección de errores recurrentes de tono, personalización, gramática y sesgos.
- APIs:
  - `GET /api/nlp/user-edit-analysis`
  - `GET /api/nlp/systemic-analysis`
  - `POST /api/nlp/export-training-dataset`
- CLI de análisis en `backend/scripts/analyze_edited_responses.py`.

## Quick start local

Desde `backend/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```

Esto instala dependencias, ejecuta migraciones, crea un usuario local de prueba y levanta la API.

## Endpoints principales

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/locations` | Lista ubicaciones disponibles para onboarding (`user_id`) |
| `GET` | `/oauth/google/start` | Inicia OAuth (`user_id`, opcional `location_id`) |
| `GET` | `/oauth/google/callback` | Callback OAuth |
| `POST` | `/webhooks/google/reviews` | Webhook Pub/Sub para nuevas reseñas |
| `GET` | `/starter/onboarding` | Pantalla inicial Starter |
| `GET` | `/starter/connect-google` | Redirección a OAuth con contexto Starter |
| `GET` | `/starter/loading` | Pantalla de carga del onboarding |
| `GET` | `/starter/tone-selector` | Selector de tono + activación Starter |
| `GET` | `/starter/dashboard` | Dashboard Starter |
| `GET` | `/starter/profile` | Configuración de perfil Starter |
| `POST` | `/api/starter/profile` | Guarda tono, palabras prohibidas y schedule |
| `GET` | `/starter/subscription` | Vista de suscripción y facturación |
| `GET` | `/api/subscription/status` | Resumen de suscripción |
| `GET` | `/api/subscription/invoices` | Facturas Stripe |
| `GET` | `/api/subscription/upgrade-check` | Verifica si requiere upgrade |
| `POST` | `/api/subscription/upgrade/growth` | Crea checkout Growth |
| `GET` | `/starter/approvals` | UI de aprobación manual |
| `GET` | `/api/reviews/pending` | Reseñas pendientes de aprobación |
| `POST` | `/api/reviews/{id}/approve` | Aprueba y envía respuesta |
| `POST` | `/api/reviews/{id}/regenerate` | Regenera respuesta sugerida |
| `POST` | `/api/tone-preview` | Preview del tono |
| `POST` | `/api/tone/set` | Guarda tono preferido |
| `POST` | `/api/starter/activate` | Activa Starter con flags operativos |
| `GET` | `/api/tone/current` | Lee tono preferido actual |
| `GET` | `/starter/report` | Reporte mensual renderizado |
| `GET` | `/api/reports/monthly-sentiment` | Sentimiento mensual |
| `GET` | `/api/reports/monthly` | Payload persistido del reporte |
| `GET` | `/api/reports/monthly-pdf` | Estado y signed URL del PDF mensual |
| `GET` | `/api/reports/history` | Histórico mensual |
| `GET` | `/api/nlp/starter-tip-of-day` | Tip del Día para dashboard Starter |
| `GET` | `/api/cancellation/impact-data` | Impacto previo a cancelación |
| `POST` | `/api/cancellation/initiate` | Inicia flujo de cancelación |
| `POST` | `/api/cancellation/plan-pausa` | Activa Plan Pausa |
| `POST` | `/api/cancellation/confirm` | Confirma cancelación |
| `GET` | `/api/cancellation/grace-period-status` | Estado del grace period |
| `GET` | `/api/nlp/user-edit-analysis` | Análisis NLP por usuario |
| `GET` | `/api/nlp/systemic-analysis` | Análisis NLP sistémico |
| `POST` | `/api/nlp/export-training-dataset` | Exporta dataset de entrenamiento |

## Migraciones Alembic

| Version | Description |
|---------|-------------|
| `0001` | Esquema inicial: `users`, `google_connections`, `reviews` |
| `0002` | Columnas NLP en reviews + `business_name` |
| `0003` | Tabla `starter_monthly_metrics` |
| `0004` | `reply_approved_text` + `reply_sent_at` |
| `0005` | Tabla `monthly_reports` |
| `0006` | `preferred_tone` en `google_connections` |
| `20260418_0007` | Lifecycle + churn tracking |
| `20260418_0008` | Flags de activación Starter |
| `20260418_0009` | Campos PDF y resumen ejecutivo en `monthly_reports` |

## Tests

```powershell
# Unit tests
pytest tests/unit -q

# Integration tests
pytest tests/integration -q

# Suite específica de churn
pytest backend/tests/test_churn_system.py -v
```

## Documentación del proyecto

### Núcleo del proyecto
- `docs/README.md`
- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/DATA_MODEL.md`
- `docs/OPERATIONS.md`
- `docs/NLP_REPLY_AUTOMATION.md`

### Churn y cancelación
- `IMPLEMENTATION_CHURN_SYSTEM.md`
- `NEXT_STEPS_CHURN_IMPLEMENTATION.md`
- `CHURN_SYSTEM_ARCHITECTURE.md`
- `EXECUTIVE_SUMMARY_CHURN_SESSION5.md`
- `PRE_MIGRATION_CHECKLIST.md`
- `IMPLEMENTATION_CANCELLATION_FULLSTACK.md`
- `QUICKSTART_CANCELLATION.md`
- `GOOGLE_API_GRACE_PERIOD.md`
- `SESSION_6_COMPLETE.md`
- `DELIVERY_SUMMARY_SESSION_6.md`
- `FILES_INDEX_SESSION_6.md`

### NLP model improvement
- `backend/START_HERE.md`
- `backend/IMPLEMENTATION_COMPLETE.md`
- `backend/NLP_INITIATIVE_EXECUTIVE_SUMMARY.md`
- `backend/NLP_MODEL_IMPROVEMENT_ANALYSIS.md`
- `backend/NLP_ANALYSIS_INTEGRATION_GUIDE.md`
- `backend/NLP_ANALYSIS_SYSTEM_OVERVIEW.md`

### Backend y despliegue
- `backend/LOCAL_DEV.md`
- `backend/deploy/DEPLOYMENT.md`
- `backend/pdf-worker/README.md`

## Notas operativas

- La UI principal sigue siendo server-rendered desde FastAPI; el árbol `frontend/src` contiene componentes y hooks de referencia para el flujo de cancelación, pero no existe un build frontend separado en este workspace.
- El scheduler de `monthly_report_worker.py` ahora registra tanto el job mensual de reportes como el job de auto-reply por minuto.
- Las rutas de cancelación están montadas desde `backend/app/routes/` y requieren la instancia única de FastAPI definida en `backend/app/main.py`.

