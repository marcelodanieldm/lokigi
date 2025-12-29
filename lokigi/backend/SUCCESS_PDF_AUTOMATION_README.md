# Automatización de generación y envío de Certificado de Éxito Lokigi

## Objetivo
Generar el reporte PDF profesional en el backend, almacenarlo en Supabase Storage y notificar al cliente por email, soportando ES, PT, EN.

## Flujo Automatizado
1. **Generación de PDF**
   - Se usa `ReportLab` para crear el PDF multilingüe (ES, PT, EN) con el diseño ejecutivo.
   - Lógica en `backend/utils/success_pdf.py`.
2. **Almacenamiento en Supabase**
   - El PDF se sube automáticamente a un bucket público (`reports`) usando la API de Supabase.
   - Lógica en `backend/utils/supabase_pdf.py`.
   - La URL pública se guarda en la tabla `orders`.
3. **Notificación por Email**
   - Se envía un email de éxito al cliente con el enlace al PDF usando SendGrid (free tier).
   - Lógica en `backend/utils/email_sendgrid.py`.
4. **Endpoint único**
   - POST `/order` recibe los datos, genera el PDF, lo sube, guarda la orden y notifica al cliente.
   - Soporta idioma dinámico según el lead (`lang`).

## Ejemplo de uso
```json
POST /order
{
  "user_email": "cliente@ejemplo.com",
  "lang": "es",
  "name": "Peluquería Estilo",
  "address": "Calle Falsa 123",
  "final_score": 92,
  "improvements": ["SEO Local", "Fotos optimizadas"],
  "photos": [{"lat": -34.6, "lon": -58.4}],
  "ranking": [{"name": "Tu Negocio", "score": 92}],
  "radar_labels": ["Reputación"],
  "radar_before": [60],
  "radar_after": [92]
}
```

## Requisitos
- Variables de entorno:
  - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`
- Bucket público `reports` en Supabase Storage
- Tabla `orders` en Supabase (ver `supabase_schema.sql`)

## Archivos Clave
- `backend/main.py`: endpoint `/order`
- `backend/utils/success_pdf.py`: generación PDF
- `backend/utils/supabase_pdf.py`: subida a Storage
- `backend/utils/email_sendgrid.py`: email SendGrid
- `supabase_schema.sql`: tabla y bucket

---

**Este flujo permite entregar el Certificado de Éxito Lokigi de forma profesional, automatizada y multilingüe.**
