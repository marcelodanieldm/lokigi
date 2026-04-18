# Implementacion Growth Fase 2 - Tickets Tecnicos

Fecha: 2026-04-18

## Ticket 1 - KPI MSP (Market Share Pack)
Estado: Implementado

Objetivo:
- Medir el porcentaje de SERPs donde el cliente aparece en Top 3.

Entregables:
- Tabla `growth_serp_observations`.
- Endpoint de ingesta `POST /api/growth/serp-observations`.
- Calculo en servicio `GrowthPremiumReportService`.

Criterio de aceptacion:
- Con observaciones cargadas, `GET /api/growth/premium-report` retorna `market_share_pack_pct`.

## Ticket 2 - KPI Keyword Conquest Rate
Estado: Implementado

Objetivo:
- Medir porcentaje de keywords conquistadas en ventana temporal.

Entregables:
- Tabla `growth_keyword_conquest_events`.
- Endpoint de ingesta `POST /api/growth/keyword-conquests`.
- Calculo en servicio Premium.

Criterio de aceptacion:
- Reporte Premium retorna `keyword_conquest_rate_pct`.

## Ticket 3 - KPI Competitor Sentiment Delta
Estado: Implementado

Objetivo:
- Diferencia entre score de sentimiento cliente y promedio competidores.

Entregables:
- Reuso de `growth_sentiment_benchmark_runs`.
- Calculo en servicio Premium usando ultimo benchmark persistido.

Criterio de aceptacion:
- Reporte Premium retorna `competitor_sentiment_delta` cuando existe benchmark.

## Ticket 4 - KPI Activity Velocity Index (AVI)
Estado: Implementado (base)

Objetivo:
- Relacion de actividad cliente vs promedio competidores ponderando posts/fotos.

Entregables:
- Nuevas columnas `photos_count_total` en snapshots de cliente y competidor.
- Calculo AVI en servicio Premium.

Criterio de aceptacion:
- Reporte Premium retorna `activity_velocity_index` si hay snapshots suficientes.

## Ticket 5 - Prompt A (Correlacion posteos vs ranking)
Estado: Implementado

Objetivo:
- Exponer correlacion entre intensidad de posteo competidor y ranking cliente.

Entregables:
- Vista SQL `growth_posting_rank_correlation` creada en migracion.

Criterio de aceptacion:
- Vista disponible para consultas analiticas por `user_id`.

## Ticket 6 - Prompt B (Brecha de servicios)
Estado: Implementado

Objetivo:
- Detectar servicios ofrecidos por >=3 competidores no declarados por el cliente.

Entregables:
- Algoritmo en `GrowthPremiumReportService._compute_service_gap_analysis`.

Criterio de aceptacion:
- Reporte Premium retorna `service_gap_opportunities` priorizadas.

## Ticket 7 - Prompt C (Reporte multiubicacion)
Estado: Parcial

Objetivo:
- Soportar contraste entre ubicaciones (hasta 5).

Entregables realizados:
- Parametro `max_locations` incorporado en endpoint Premium.

Pendiente:
- Extender esquema de conexiones para multiples locations por usuario en Growth.
- Agregar agregaciones por `location_label` en payload y PDF worker.

## Ticket 8 - Prompt D (Estado de Dominio Local)
Estado: Implementado (base)

Objetivo:
- Determinar estado competitivo y alertas ejecutivas.

Entregables:
- Alerta `Cambio de Guardia` por caida de MSP entre ventanas.
- Alerta `Amenaza Detectada` por AVI bajo y delta de sentimiento negativo.

Criterio de aceptacion:
- Reporte Premium retorna bloque `alerts` con flags y severidad.

## Ticket 9 - Comparativa ROI Antes vs Hoy
Estado: Implementado

Objetivo:
- Comparar evolucion historica de rating y response rate usando reportes mensuales.

Entregables:
- Bloque `roi` en payload Premium.

Criterio de aceptacion:
- Si hay historial >=2 reportes, se retorna before/today/delta.

## Ticket 10 - Estrategia de Entrega (Retention & Upsell)
Estado: Implementado

Objetivo:
- Convertir eventos Growth en notificaciones accionables con deduplicacion, cooldown y despacho asincrono.

Entregables:
- Tabla `growth_event_notifications` para cola/registro de eventos multi-canal (`push`, `email`, `in_app`).
- Endpoint interno `POST /internal/growth/events/publish` para publicar eventos `guard_change`, `threat_detected`, `roi_snapshot`.
- Endpoints de lectura UX: `GET /api/growth/events` y `POST /api/growth/events/{event_id}/seen`.
- Servicio `GrowthEventNotificationService` con:
	- dedupe 24h por `dedupe_key`
	- cooldown para push critico/alto (max 2 por 24h)
	- enrutamiento por evento y dispatch asincrono por scheduler
- Job programado cada minuto: `run_growth_event_notifications_dispatch`.

Criterio de aceptacion:
- Publicar un evento crea filas `pending` por canal permitido y evita duplicados en ventana de 24h.
- El scheduler procesa la cola y deja eventos en `sent` o `failed` con trazabilidad de intentos.

## Endpoints nuevos
- `POST /api/growth/serp-observations`
- `POST /api/growth/keyword-conquests`
- `GET /api/growth/premium-report?user_id=<uuid>&window_days=30&max_locations=5`
- `POST /internal/growth/events/publish`
- `GET /api/growth/events?user_id=<uuid>&include_seen=false&limit=30`
- `POST /api/growth/events/{event_id}/seen?user_id=<uuid>`

## Prompts operativos parametrizados (A-D)
- Prompt A (Data Analyst): define vista SQL de correlacion `frecuencia_posteos_competencia` vs `posicion_ranking_cliente`, con deltas 7d/14d y regla de negocio para `Cambio de Guardia`.
- Prompt B (Data Science/BI): genera seccion `Analisis de Brecha` detectando servicios presentes en >=3 competidores y ausentes en el perfil del cliente, con recomendacion accionable.
- Prompt C (Backend): guia de optimizacion del worker PDF para volumen 10x, soporte multiubicacion (hasta 5), radar competitivo dinamico y fallback de render.
- Prompt D (UI/UX): define pagina `Estado de Dominio Local` con heatmap de zonas/keywords e iconografia de trofeo/alerta.

Variables globales recomendadas para template engine:
- `company_name`, `period_label`, `window_days`, `max_locations`, `load_multiplier`
- `target_keywords`, `top_competitors`, `sql_engine`, `chart_library`, `page_format`

## Notas operativas
- Ejecutar migraciones antes de usar nuevos endpoints.
- Los KPIs MSP y Conquest dependen de carga de eventos SERP/conquest.
- AVI usa posts y fotos; si fotos es nulo, se usa valor 0 como fallback.
- Para mantener limpio el repositorio del worker PDF, no versionar `backend/pdf-worker/node_modules/`.

## Estado de validacion tecnica
- Backend Python: compilacion de modulos modificados OK y rutas nuevas detectadas en FastAPI.
- PDF worker TypeScript: validacion de build bloqueada por entorno local inconsistente de `node_modules` y errores de instalacion de Puppeteer (descarga de browser + espacio en disco).
- Accion recomendada para reproducir build del worker en limpio:
	- borrar `backend/pdf-worker/node_modules`
	- reinstalar con `PUPPETEER_SKIP_DOWNLOAD=true npm install`
	- ejecutar `npm run build`
