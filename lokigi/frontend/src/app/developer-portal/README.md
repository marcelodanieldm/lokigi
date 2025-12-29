# Lokigi Developer Portal

## Objetivo
Portal técnico para que cualquier programador integre Lokigi en 5 minutos. Inspirado en Swagger/Redoc, con dark mode, verde neón y enfoque minimalista/técnico.

## Estructura
- **Sidebar.tsx**: Navegación lateral.
- **ApiDocs.tsx**: Documentación API con ejemplos y syntax highlighting (Python, JS, PHP).
- **ApiKeyManager.tsx**: Gestión de API Keys (generar, revocar, ver consumo).
- **UsageCharts.tsx**: Gráficos de consumo diario (bar chart).
- **page.tsx**: Layout principal.

## Tecnologías
- Next.js (App Router)
- Tailwind CSS (dark mode, verde neón)
- react-syntax-highlighter (código)
- react-chartjs-2 + chart.js (gráficos)

## Estética
- Dark mode por defecto.
- Verde neón (#39FF14) para acentos y gráficos.
- Tipografía técnica, bloques de código y navegación clara.

## Personalización
- Cambia ejemplos de código y endpoints en `ApiDocs.tsx`.
- Integra backend real para API Keys y consumo en `ApiKeyManager.tsx` y `UsageCharts.tsx`.

## Uso
1. Instala dependencias:
   ```bash
   npm install react-syntax-highlighter react-chartjs-2 chart.js
   ```
2. Accede a `/developer-portal` en tu frontend.
3. Personaliza según tus necesidades.

---

> Sugerencia: Integra autenticación y conecta los componentes a tu backend para producción.
