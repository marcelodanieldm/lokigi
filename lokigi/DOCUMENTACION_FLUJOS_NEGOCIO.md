# Documentación de Flujos, Modelo de Negocio y Tipos de Usuario

## 1. Modelo de Negocio: Lokigi SaaS

Lokigi es una plataforma SaaS de inteligencia de negocios locales. Ofrece dashboards, alertas, reportes y automatización de marketing para negocios, consultores y agencias. El modelo es freemium con upgrades premium y funcionalidades avanzadas para usuarios de pago.

- **Freemium:** Acceso básico a reportes y alertas limitadas.
- **Premium:** Acceso completo a dashboards, reportes avanzados, growth projections, alertas multilingües, y herramientas de marketing automatizado.
- **Agencias/Consultores:** Acceso multi-cuenta, reportes de impacto, herramientas de auditoría y gestión de clientes.
- **Monetización:** Suscripción mensual/anual vía Stripe, upgrades in-app, y servicios adicionales (consultoría, integraciones).

## 2. Tipos de Usuario

| Tipo de Usuario   | Descripción | Features principales |
|-------------------|-------------|---------------------|
| Invitado          | Usuario anónimo, acceso limitado a landing y demo. | Landing pública, demo de auditoría, registro. |
| Usuario Básico    | Registrado, plan gratuito. | Reportes básicos, alertas limitadas, acceso a landing privada. |
| Usuario Premium   | Suscripción activa. | Dashboard premium, growth projection, alertas avanzadas, PDF, marketing automation, ROI tracker, dark mode, mobile-first. |
| Superusuario      | Admin, consultor, agencia. | Multi-cuenta, gestión de clientes, reportes de impacto, auditoría avanzada, acceso a todos los features. |

## 3. Flujos Principales (2025)

### a) Registro y Onboarding
- Acceso vía landing pública.
- Registro con email/Supabase Auth.
- Onboarding guiado según tipo de usuario.

### b) Generación de Reporte de Impacto
- Usuario solicita auditoría.
- Backend ejecuta análisis (growth, alertas, lead scoring).
- Se genera PDF y dashboard interactivo.
- Usuario recibe notificación y acceso al reporte.

### c) Dashboard Premium
- Acceso solo para usuarios premium.
- Visualización de heatmap, alertas, ROI tracker.
- Modo oscuro neón, mobile-first.
- Acceso a growth projection y reportes descargables.

### d) Automatización de Marketing (Outreach Engine)
- Superusuario/premium configura campañas.
- Generación automática de links, mensajes y seguimiento.
- QA Automation valida links, I18n y tracking de conversión.
- Resultados y métricas en dashboard.

### e) QA Automation y Analytics
- Todos los flujos críticos tienen tests automatizados (Pytest, Playwright).
- QA para links, I18n, funnel, persistencia y permisos.
- Resultados visibles en CI/CD y logs.

### f) Gestión de Permisos y Persistencia
- Middleware en frontend y backend valida permisos según tipo de usuario.
- Persistencia de preferencias, reportes y métricas en Supabase.

## 4. Features por Tipo de Usuario

- **Invitado:**
  - Acceso a landing pública y demo de auditoría.
  - Registro y upgrade a usuario básico.
- **Usuario Básico:**
  - Reportes básicos, alertas limitadas.
  - Acceso a landing privada y upgrade a premium.
- **Usuario Premium:**
  - Dashboard premium, growth projection, alertas avanzadas.
  - Generación de PDF, marketing automation, ROI tracker.
  - Acceso a dark mode y mobile-first UX.
- **Superusuario/Agencia:**
  - Multi-cuenta, gestión de clientes.
  - Auditoría avanzada, reportes de impacto.
  - Acceso a todas las features y configuraciones avanzadas.

## 5. Referencias de Implementación

- **Backend:** FastAPI, growth_projection.py, alert_radar.py, outreach_engine.py, lead_scoring.py
- **Frontend:** Next.js, PremiumControlTower, PublicAuditLanding, middleware.ts
- **QA:** tests/test_marketing_conversion.py, QA_MARKETING_CONVERSION_README.md, test_dashboard_premium.py
- **CI/CD:** .github/workflows/qa_global_validator.yml

---
Última actualización: 2025-12-29
