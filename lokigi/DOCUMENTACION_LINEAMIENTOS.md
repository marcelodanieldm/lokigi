# Lineamientos de Documentación para Lokigi

Este documento resume las mejores prácticas y ejemplos para documentar componentes, hooks, utilidades, scripts y archivos SQL en el proyecto Lokigi.

---

## 1. Componentes de Frontend (Next.js/TypeScript)

```tsx
/**
 * ImpactReport.tsx
 * Componente para mostrar el informe de impacto de Lokigi.
 * Props:
 *  - score: número de score actual
 *  - improvements: lista de mejoras realizadas
 *  - photos: fotos optimizadas con geotag
 *  - ranking: ranking de competidores
 *  - radarData: datos para gráfico radar
 */
```

Coloca este tipo de encabezado al inicio de cada archivo de componente. Explica el propósito y las props principales.

---

## 2. Hooks y Utilidades

```ts
/**
 * useSuperuser.ts
 * Hook para determinar si el usuario autenticado es superusuario.
 * Retorna: booleano
 */
```

Describe el propósito del hook o utilidad y su valor de retorno.

---

## 3. Scripts de Supabase

```ts
// monthly_competitor_scrape/index.ts
// Edge Function para Supabase: ejecuta scraping y actualización mensual por suscriptor.
// Usa supabase-js v2 y node-fetch.
```

Incluye un resumen de la función y dependencias clave.

---

## 4. Archivos SQL

```sql
-- supabase_schema.sql
-- Define tablas para puntos de visibilidad y ROI Tracker.
-- Incluye índices para optimizar consultas.
```

Explica el propósito de cada tabla y los índices.

---

## 5. Recomendaciones Generales
- Usa comentarios JSDoc en TypeScript/JavaScript.
- Usa docstrings en Python.
- Explica la lógica principal y los parámetros importantes.
- Mantén los encabezados actualizados si cambian las props o la lógica.

---

Este documento puede ser usado como referencia rápida para mantener la documentación consistente y profesional en todo el proyecto.
