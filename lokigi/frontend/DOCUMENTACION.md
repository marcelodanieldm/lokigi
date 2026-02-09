# Documentación Frontend Lokigi

## Índice
- [Visión General](#visión-general)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Tipos de Usuario y Flujos](#tipos-de-usuario-y-flujos)
- [Features por Tipo de Usuario](#features-por-tipo-de-usuario)
- [Componentes y Rutas](#componentes-y-rutas)
- [Guía de Estilos y UI](#guía-de-estilos-y-ui)
- [Manual de Implementación](#manual-de-implementación)

---

## Visión General
Lokigi es una plataforma SaaS multi-tenant para gestión, auditoría y crecimiento de negocios locales. El frontend está construido en Next.js + TypeScript + Tailwind CSS, con un diseño profesional, claro y corporativo.

## Estructura del Proyecto
- `/frontend/src/app/` — Páginas principales y rutas
- `/frontend/src/app/components/` — Componentes reutilizables
- `/frontend/src/app/utils/` — Utilidades y hooks
- `/frontend/public/` — Recursos estáticos
- `/frontend/messages/` — Internacionalización

## Tipos de Usuario y Flujos

### 1. Usuario Invitado (No autenticado)
- Acceso: Landing principal, documentación pública, branding, soporte, FAQ, integraciones.
- Flujos:
  - Visualizar landing y marketing.
  - Consultar documentación API pública.
  - Acceder a recursos de ayuda y contacto.
  - Iniciar proceso de registro/login.

### 2. Usuario Registrado (Cliente estándar)
- Acceso: Dashboard, Impact Report, Premium Dashboard (si tiene acceso), perfil, integraciones.
- Flujos:
  - Login seguro vía SupabaseAuthPanel.
  - Visualizar y descargar Impact Report.
  - Acceder a panel de control con métricas, alertas y recomendaciones.
  - Consultar y gestionar integraciones (Zapier, Make.com, HubSpot).
  - Editar perfil y configuración personal.

### 3. Usuario Premium
- Acceso: Todo lo anterior + Premium Control Tower, Growth Projection, ROI Tracker, alertas avanzadas.
- Flujos:
  - Acceso a dashboards premium con heatmaps, proyecciones y análisis avanzados.
  - Visualizar y gestionar alertas personalizadas.
  - Acceso prioritario a soporte y recursos exclusivos.

### 4. Superusuario / Admin
- Acceso: Todo lo anterior + paneles de administración, proyección de crecimiento avanzada, gestión de usuarios y features experimentales.
- Flujos:
  - Acceso a SuperuserGrowthProjection y WorkerDashboard.
  - Gestión de usuarios, features y monitoreo avanzado.
  - Acceso a logs, métricas globales y configuraciones avanzadas.

### 5. Desarrollador (Developer Portal)
- Acceso: Developer Portal, API Docs, gestión de API Keys, visualización de consumo.
- Flujos:
  - Generar, revocar y consultar API Keys.
  - Visualizar documentación Swagger/Redoc.
  - Consultar consumo de API y métricas técnicas.

## Features por Tipo de Usuario

| Feature                        | Invitado | Cliente | Premium | Superusuario | Dev Portal |
|--------------------------------|----------|---------|---------|--------------|------------|
| Landing y marketing            | ✔        | ✔       | ✔       | ✔            | ✔          |
| Dashboard estándar             |          | ✔       | ✔       | ✔            |            |
| Impact Report                  |          | ✔       | ✔       | ✔            |            |
| Premium Control Tower          |          |         | ✔       | ✔            |            |
| Growth Projection              |          |         | ✔       | ✔            |            |
| ROI Tracker                    |          |         | ✔       | ✔            |            |
| Alertas avanzadas              |          |         | ✔       | ✔            |            |
| Superuser features             |          |         |         | ✔            |            |
| Integraciones externas         | ✔        | ✔       | ✔       | ✔            |            |
| Perfil y configuración         |          | ✔       | ✔       | ✔            |            |
| Developer Portal (API, Keys)   |          |         |         |              | ✔          |
| Soporte y FAQ                  | ✔        | ✔       | ✔       | ✔            | ✔          |

## Componentes y Rutas
- `Dashboard`: `/dashboard/`
- `Premium Dashboard`: `/dashboard/premium/`
- `Impact Report`: `/impact-report/`
- `Developer Portal`: `/developer-portal/`
- `API Docs`: `/developer-portal/api-docs/`
- `API Keys`: `/developer-portal/api-keys/`
- `Consumo API`: `/developer-portal/usage/`
- `Perfil`: `/profile/`
- `Integraciones`: `/integrations/`
- `Soporte`: `/support/`
- `FAQ`: `/faq/`
- `Branding`: `/branding/`
- `Errores`: `/404`, `/500`

## Guía de Estilos y UI
- Paleta: Azul corporativo, gris claro, blanco, acentos sobrios.
- Tipografía: Sans-serif profesional.
- Componentes: Tarjetas blancas, bordes grises, botones azules, iconografía elegante (Heroicons).
- Sin dark mode ni neón.

## Manual de Implementación
1. Instalar dependencias: `npm install`
2. Configurar variables de entorno (`.env.local`)
3. Ejecutar en desarrollo: `npm run dev`
4. Desplegar: `npm run build` y `npm start` o vía Vercel
5. Personalizar branding en `/branding/`
6. Consultar Developer Portal para integraciones API

---

> Para detalles de cada componente, consulta los comentarios en el código fuente de cada archivo en `/components/` y `/app/`.
