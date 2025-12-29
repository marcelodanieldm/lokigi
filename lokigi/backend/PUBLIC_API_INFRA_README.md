# Lokigi Public API Infraestructura: Endpoints, Webhooks y Facturación

## 1. API Key Management
- **POST /api-keys/generate**: Genera una nueva API Key (requiere user_id, label opcional, tier opcional).
- **GET /api-keys/list/{user_id}**: Lista todas las API Keys activas del usuario.
- **POST /api-keys/revoke/{key_id}**: Revoca una API Key.
- Seguridad: Las API Keys se almacenan hasheadas (SHA256) en Supabase. Nunca se expone el hash.

## 2. Endpoint de Auditoría Externa
- **GET /api/v1/audit?business_id=...&lang=es&currency=EUR**
  - Headers: `x-api-key: TU_API_KEY`
  - Respuesta: JSON minificado con score, revenue perdido, top 3 acciones y metadatos.
  - Autenticación: API Key real, validada contra hash en Supabase.
  - Rate limiting dinámico según el tier de la API Key.
  - Cada llamada incrementa el uso de créditos y puede disparar facturación por exceso.

## 3. Auditoría Asíncrona y Webhooks
- **POST /audit**: Inicia una auditoría asíncrona (IA + Dominance). Devuelve audit_id inmediato.
  - Headers: `x-api-key: TU_API_KEY`
  - Body: Datos de negocio y competencia.
  - El resultado se cachea y puede consultarse vía **GET /audit/result/{audit_id}**.
  - Al completarse, se dispara un webhook a todas las URLs registradas para el evento `audit.completed` del usuario.
- **POST /webhooks/register** (próximamente): Registra una URL de webhook para eventos (audit.completed, etc).

## 4. Facturación por Exceso de Créditos (Overage Billing)
- Cada API Key tiene un límite mensual de créditos (`api_credits`).
- Si se supera el límite, se factura automáticamente vía Stripe (invoice + invoice item) usando el customer_id del usuario.
- Los eventos de facturación se registran en `api_billing_events`.

## 5. Seguridad y Buenas Prácticas
- Todas las API Keys deben mantenerse secretas. Nunca compartas tu key en público.
- Los webhooks deben validar la autenticidad de los eventos recibidos.
- El endpoint de auditoría y los webhooks están protegidos por autenticación y rate limiting.

## 6. Ejemplo de Flujo Completo
1. El usuario genera una API Key desde el portal.
2. Integra la API Key en su sistema (Zapier, Make, etc).
3. Realiza llamadas a /api/v1/audit o inicia auditorías asíncronas.
4. Si se supera el límite de créditos, se factura automáticamente.
5. Al completarse una auditoría, recibe notificación vía webhook.

---

> Consulta el código en backend/api_key_manager.py, billing_middleware.py, webhook_engine.py y public_api.py para detalles de implementación.
> Personaliza los límites, eventos y lógica de facturación según tu modelo de negocio.
