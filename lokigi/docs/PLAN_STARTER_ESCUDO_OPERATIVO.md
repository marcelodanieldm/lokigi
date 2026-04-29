# Plan Starter ($39/mes): El Escudo Operativo

## Objetivo
Automatizar presencia y reputacion del negocio con minima intervencion manual.

## Features Clave

### 1) AI Auto-Responder
- Genera borradores de respuesta automaticamente cuando entra una reseña.
- Respeta la Voz de Marca configurada por el cliente.
- Soporta aprobacion manual o auto-envio segun configuracion operativa.

Endpoints relacionados:
- `POST /webhooks/google/reviews`
- `GET /api/reviews/pending`
- `POST /api/reviews/{review_id}/approve`
- `POST /api/reviews/{review_id}/regenerate`

### 2) Sentiment Alert (< 3 estrellas)
- Si entra una reseña con rating menor a 3, se activa alerta inmediata.
- Se registra alerta operativa interna y, opcionalmente, notificacion webhook externa.

Configuracion:
- `NEGATIVE_REVIEW_ALERT_WEBHOOK_URL`
- `NEGATIVE_REVIEW_ALERT_WEBHOOK_TOKEN`

### 3) Voz de Marca Configurable
- Perfiles soportados: Formal, Amistoso, Moderno.
- Alias tecnico: Amistoso se normaliza a `cercano` internamente.

Endpoints relacionados:
- `POST /api/tone-preview`
- `POST /api/tone/set`
- `POST /api/starter/profile`

### 4) Dashboard de Reputacion
- Visualiza nota media, volumen de reseñas y pendientes de aprobacion.
- Incluye insight de sentimiento y concepto principal del mes.

Vista:
- `GET /starter/dashboard?user_id={uuid}`

### 5) Reporte Operativo Mensual (PDF)
- Generacion mensual automatica.
- Historial por usuario y estado de PDF disponible desde backend.

Endpoints relacionados:
- `GET /api/reports/monthly`
- `GET /api/reports/monthly-pdf`
- `GET /api/reports/history`
- `GET /starter/report?user_id={uuid}&year={yyyy}&month={mm}`

## Flujos

### A) Onboarding Starter
1. Login/Conexion Google (OAuth).
2. Seleccion de 1 ubicacion (en Starter no se permite multi-ubicacion).
3. Test de Voz de Marca con reseña previa.
4. Activacion operativa (aprobacion manual y alertas).

Endpoints y vistas:
- `GET /oauth/google/start`
- `GET /oauth/google/callback`
- `GET /starter/onboarding`
- `POST /api/tone-preview`
- `POST /api/starter/activate`

### B) Gestion de Reseña
1. Google envia webhook de nueva reseña.
2. Worker/logica analiza rating y contenido.
3. IA genera borrador con tono de marca.
4. Usuario aprueba o sistema auto-envia segun regla.
5. Publicacion en Google Maps.

Endpoints:
- `POST /webhooks/google/reviews`
- `GET /api/reviews/pending`
- `POST /api/reviews/{review_id}/approve`

## Beneficios del Flujo Starter

- Valor percibido: el usuario siente que tiene un asistente que redacta por el y reduce la friccion operativa frente a cada reseña nueva.
- Control: el paso de aprobacion le da seguridad antes de publicar en su perfil oficial y mantiene supervision humana cuando la reputacion esta en juego.
- Eficiencia bare-metal: al ejecutarse localmente con Celery, los borradores se generan en segundos y permiten responder reseñas mientras el usuario sigue con su operacion diaria.

### C) Desuscripcion
1. Boton "Pausar" (Plan Pausa) como estrategia de retencion.
2. Encuesta rapida de churn.
3. Exportacion de historial de reseñas en CSV.
4. Cierre de sesion.

Endpoints:
- `POST /api/cancellation/initiate`
- `POST /api/cancellation/plan-pausa`
- `POST /api/cancellation/confirm`
- `GET /api/cancellation/export-reviews.csv`
- `POST /api/cancellation/logout`

## Notas de Operacion
- El flujo de alerta inmediata se activa para rating `< 3`.
- El cierre de sesion es stateless en backend; el frontend debe limpiar estado local y redirigir.
- La exportacion CSV esta pensada para cumplir salida asistida antes de cierre.
