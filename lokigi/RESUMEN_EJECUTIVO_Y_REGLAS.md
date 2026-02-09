# Resumen Ejecutivo, Flujos y Reglas de Negocio

## Resumen Ejecutivo
Lokigi es una plataforma integral para la gestión, análisis y visualización de datos de presencia digital y reputación de negocios. Combina un backend en Python (FastAPI) y un frontend en Next.js/TypeScript, integrando servicios como Supabase y Stripe para autenticación, almacenamiento y pagos. El sistema está diseñado para ser modular, escalable y fácil de desplegar en la nube o localmente.

## Flujos Principales

### 1. Autenticación y Acceso
- El usuario se registra o inicia sesión mediante Supabase Auth.
- El frontend verifica el rol del usuario (cliente, premium, superuser) y muestra el dashboard correspondiente.

### 2. Dashboard Premium
- Usuarios premium acceden a un dashboard con:
  - Heatmap de visibilidad (mapa interactivo con puntos de dominio propio y de competidores).
  - Feed de alertas generadas por el motor de alertas del backend.
  - ROI Tracker: seguimiento del retorno de inversión mensual.

### 3. Generación de Reportes
- El usuario puede solicitar un Impact Report, que muestra:
  - Score actual y mejoras realizadas.
  - Fotos optimizadas con geotag.
  - Ranking frente a competidores.
  - Gráficos radar de evolución de métricas.

### 4. Proyección de Crecimiento
- El usuario ingresa métricas iniciales y finales, y el sistema proyecta el crecimiento y el impacto económico estimado a 6 meses.

### 5. Alertas Competitivas
- El backend analiza snapshots mensuales de competidores y genera alertas si detecta cambios relevantes (ej: aumento de rating, nuevas fotos, más reseñas).
- Las alertas se muestran en tiempo real en el dashboard.

### 6. Pagos y Suscripciones
- Stripe gestiona los pagos y actualiza el estado de la suscripción en Supabase mediante webhooks.
- El acceso premium se habilita/deshabilita automáticamente según el estado de pago.

---

## Reglas de Negocio

- Solo usuarios con rol "PREMIUM" o "SUPERUSER" pueden acceder a dashboards avanzados y reportes de impacto.
- Las alertas competitivas se generan solo si hay cambios significativos en las métricas de los competidores.
- El ROI Tracker solo considera datos de usuarios activos y pagos confirmados.
- El sistema debe proteger endpoints críticos y validar roles en cada request.
- Los reportes y proyecciones deben ser claros, visuales y exportables (PDF, imagen).
- El scraping y actualización de datos de competidores se realiza de forma mensual y automatizada.
- Las variables de entorno sensibles (claves API, secretos) nunca deben subirse al repositorio.

---

## Notas
- Para detalles técnicos, ver README.md y DOCUMENTACION_LINEAMIENTOS.md.
- Para flujos visuales, se recomienda usar diagramas BPMN o herramientas como Whimsical/Lucidchart.

---

Este documento debe mantenerse actualizado ante cualquier cambio relevante en la lógica o alcance del sistema.
