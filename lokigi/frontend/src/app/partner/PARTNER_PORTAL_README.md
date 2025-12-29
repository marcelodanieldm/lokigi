# Partner Portal (Affiliate Dashboard) - Documentación UX/UI

## Objetivo
Proveer a los socios/afiliados una interfaz profesional para visualizar métricas clave y acceder a materiales de marketing.

## Secciones del Dashboard

### 1. Métricas Clave
- **Clics:** Total de clics en el link de afiliado.
- **Leads Generados:** Número de registros/conversiones atribuidos.
- **Comisiones Totales:** Suma de comisiones acumuladas (en USD o moneda local).
- Visualización con verde neón y dark mode.

### 2. Link Generator
- Input con el link único del afiliado (copiable con un click).
- Botón para copiar el link.
- Generador de QR (imagen) para imprimir en volantes físicos.

### 3. Media Kit
- Lista de enlaces para descargar banners, capturas de pantalla de reportes 'antes/después', etc.
- Archivos alojados en Supabase Storage o CDN.

## Estética
- Fondo oscuro (`bg-gray-950`), acentos en verde neón (`text-green-400`, `border-green-400`).
- Tipografía técnica, layout profesional y responsivo.

## Ejemplo de Uso
```tsx
import AffiliateDashboard from './AffiliateDashboard';

<AffiliateDashboard
  clicks={123}
  leads={12}
  commissions={456.78}
  affiliateLink="https://lokigi.com/?ref=abc123"
  qrCodeUrl="https://api.qrserver.com/v1/create-qr-code/?data=https://lokigi.com/?ref=abc123"
  mediaKitLinks={[
    { label: 'Banner 728x90', url: 'https://cdn.lokigi.com/banners/728x90.png' },
    { label: 'Antes/Después', url: 'https://cdn.lokigi.com/screenshots/before-after.png' },
  ]}
/>
```

## Buenas Prácticas
- El QR debe ser legible en impresos.
- El Media Kit debe actualizarse periódicamente.
- El dashboard debe ser mobile-first y rápido.

---
Última actualización: 2025-12-29
