# Lokigi Marketplace (Frontend Bootstrap)

Este frontend es 100% estático, sin dependencias de Node.js ni Next.js. Puedes desplegarlo en cualquier hosting estático (Netlify, Vercel, S3, Supabase Storage, etc.)

## Estructura
- `index.html`: Página principal del marketplace, usa Bootstrap 5 y modo oscuro.
- `marketplace.js`: Lógica para consumir la API del backend (FastAPI) y renderizar apps.
- `funnel/index.html`: Home pública del funnel comercial del cliente.
- `funnel/audit.html`: Vista de auditoría con score, fallos y CTA comercial.
- `funnel/success.html`: Confirmación de compra y siguientes pasos.
- `funnel/funnel.js`: Estado demo del recorrido lead → auditoría → success.

## Cómo probar localmente
1. Asegúrate de tener el backend corriendo en `http://localhost:8000` (o cambia la URL en `marketplace.js`).
2. Abre `frontend/static/index.html` en tu navegador.
3. ¡Listo! Verás el marketplace y podrás instalar apps.
4. Si quieres revisar el funnel comercial del cliente, abre `frontend/static/funnel/index.html`.

## Personalización
- Cambia el endpoint de la API en `marketplace.js` si tu backend está en otra URL.
- Puedes agregar más páginas, componentes o lógica JS según lo necesites.

---

**Este frontend es portable y serverless. No requiere Node.js, npm ni ningún build.**
