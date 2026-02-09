# Dashboard Premium: Interactivo y Edge Functions

## Objetivo
Visualización en tiempo real del Heatmap y automatización de scraping de competencia para clientes premium.

## Implementación

### 1. Interactive Heatmap
- Componente `PremiumControlTower` y `MapHeatmap` usan Leaflet para renderizar puntos de visibilidad desde Supabase.
- Los datos se obtienen vía utilidades en `frontend/src/app/utils/dashboardData.ts`.
- Mobile-first, dark mode, gráficos instantáneos con Tailwind.

### 2. Edge Functions (Cron Jobs)
- Supabase Edge Function `monthly_competitor_scrape` ejecuta scraping y actualización mensual para cada suscriptor activo.
- Llama al backend FastAPI para scraping y actualización de dashboard.
- Se programa vía Supabase Dashboard (cron: 0 0 1 * *).

### 3. Estado de Suscripción
- Middleware en `frontend/src/middleware.ts` bloquea acceso a /dashboard/premium si el pago de Stripe falla.
- Consulta el estado de suscripción en Supabase/Stripe.

### 4. Optimización
- Tailwind y carga dinámica de mapas para máxima velocidad y experiencia mobile.

## Archivos Clave
- `frontend/src/app/components/PremiumControlTower.tsx` y `MapHeatmap.tsx`: UI interactiva.
- `frontend/src/app/utils/dashboardData.ts`: Fetch de datos desde Supabase.
- `frontend/src/middleware.ts`: Protección de rutas premium.
- `supabase/functions/monthly_competitor_scrape/index.ts`: Edge Function para scraping mensual.

## Despliegue
- Configura variables de entorno de Supabase y Stripe en Vercel y Supabase.
- Programa la Edge Function desde el panel de Supabase Functions.

---

**Full Stack Developer: Dashboard y Edge Functions listos para producción.**
