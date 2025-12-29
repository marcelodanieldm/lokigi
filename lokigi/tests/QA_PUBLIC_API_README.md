# QA Automation: Validador de Integración Extrema para Lokigi API Pública

## Objetivo
Garantizar que la API sea indestructible, rápida y segura ante cualquier integración externa.

## Pruebas incluidas

### 1. Load Testing
- Simula 1,000 peticiones concurrentes a `/api/v1/audit`.
- Verifica que el tiempo de respuesta sea < 500ms y que todas respondan 200 OK.

### 2. Security Injection Test
- Llama a la API con llaves expiradas, malformadas y de otros usuarios.
- Espera siempre 401 Unauthorized.

### 3. Documentation Sync
- Ejecuta el ejemplo de código del portal de desarrolladores y compara la respuesta real con la estructura documentada.

### 4. Stripe Integration Test
- Llama a la API y verifica que el contador de créditos (`api_credits`) se descuente correctamente.
- (Requiere acceso a Supabase o endpoint admin para validar el contador.)

### 5. Webhook Delivery Test
- Simula el registro y recepción de webhooks al completar una auditoría.
- Usa monkeypatch para interceptar el envío y validar el payload recibido.

### 6. Rate Limiting Test
- Realiza más peticiones de las permitidas por el tier de la API Key.
- Espera recibir 429 Too Many Requests al superar el límite.

## Ejecución

```bash
pytest tests/test_public_api_extreme.py
```

> Para pruebas de carga real, se recomienda correr en entorno local o staging, no en producción.

## Notas
- Personaliza las API Keys de prueba en el archivo según tu entorno.
- La consulta de créditos en Stripe/Supabase debe implementarse según tu backend.
- Puedes ampliar la suite con pruebas de webhooks, rate limiting y edge cases adicionales.
