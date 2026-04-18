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

## Endpoints nuevos
- `POST /api/growth/serp-observations`
- `POST /api/growth/keyword-conquests`
- `GET /api/growth/premium-report?user_id=<uuid>&window_days=30&max_locations=5`

## Notas operativas
- Ejecutar migraciones antes de usar nuevos endpoints.
- Los KPIs MSP y Conquest dependen de carga de eventos SERP/conquest.
- AVI usa posts y fotos; si fotos es nulo, se usa valor 0 como fallback.

## Estado de validacion tecnica
- Backend Python: compilacion de modulos modificados OK y rutas nuevas detectadas en FastAPI.
- PDF worker TypeScript: validacion de build bloqueada por entorno local inconsistente de `node_modules` y errores de instalacion de Puppeteer (descarga de browser + espacio en disco).
- Accion recomendada para reproducir build del worker en limpio:
	- borrar `backend/pdf-worker/node_modules`
	- reinstalar con `PUPPETEER_SKIP_DOWNLOAD=true npm install`
	- ejecutar `npm run build`
