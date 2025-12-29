# Retargeting Engine - Documentación de Automatización de Mensajería y Colas

## Objetivo
Automatizar el seguimiento a leads con tres impactos programados y cancelar el flujo si el usuario compra. Usa FastAPI, Supabase Edge Functions, SendGrid y Twilio.

## Flujos Automatizados
- **T+1 hora:** Email/WhatsApp con PDF del reporte.
- **T+24 horas:** Email/WhatsApp con cupón de descuento dinámico.
- **T+7 días:** Email/WhatsApp con testimonio de éxito.
- **Cancelación automática:** Si se recibe un webhook de Stripe (checkout.session.completed), se cancela el flujo de seguimiento.

## Componentes Técnicos
- **Supabase Edge Functions:** Scheduling y persistencia de la cola (`followup_queue`).
- **SendGrid:** Envío de emails (PDF, cupón, testimonio).
- **Twilio:** Envío de WhatsApp (PDF, cupón, testimonio).
- **Stripe Webhook:** Cancela el flujo si el usuario compra.

## Endpoints FastAPI
- `POST /retargeting/schedule`: Programa los tres impactos para un lead.
- `POST /retargeting/cancel`: Cancela todos los impactos pendientes para un usuario.
- `POST /webhook/stripe`: Webhook para eventos de Stripe (cancela si hay compra).

## Edge Function/Worker
- Ejecutar `process_followup_queue()` cada minuto (cron/Edge Function).
- Envía los mensajes pendientes y marca como enviados.

## Variables de Entorno
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- `SENDGRID_API_KEY`
- `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_FROM`

## Ejemplo de Uso
```python
from backend.retargeting_engine import schedule_retargeting
schedule_retargeting(
    user_id="123",
    email="cliente@lokigi.com",
    phone="+34123456789",
    pdf_url="https://lokigi.com/reporte.pdf",
    coupon_code="LOKIGI15",
    testimonial="Juan optimizó su barbería y duplicó clientes."
)
```

## Notas
- Personaliza los mensajes y adjuntos según el flujo de negocio.
- La tabla `followup_queue` debe existir en Supabase.
- El worker puede implementarse como Edge Function, cron o Upstash Redis.

---
Última actualización: 2025-12-29
