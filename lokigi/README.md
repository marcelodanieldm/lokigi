---

## API: Dominance Index (Proximidad y Dominancia)

Endpoint: `/dominance-index` (POST)

Entrada:
```json
{
	"client": {"lat": 38.72, "lon": -9.13, "rating": 4.8, "review_count": 120, "name": "Mi Negocio"},
	"competitors": [
		{"lat": 38.723, "lon": -9.14, "rating": 4.7, "review_count": 200, "name": "Barberia Lisboa"},
		...
	],
	"locale": "pt"
}
```
Salida:
```json
{
	"dominance_index": 0.41,
	"competitor_threat": "Barberia Lisboa",
	"heatmap": [
		{"name": "Cliente", "lat": 38.7223, "lon": -9.1393, "attraction": 576.0},
		{"name": "Barberia Lisboa", "lat": 38.723, "lon": -9.14, "attraction": 1999999.999},
		...
	],
	"unit": "km"
}
```

Ver detalles y lógica en `backend/dominance_index.py` y pruebas en `tests/test_dominance_index.py`.
# Lokigi



![QA Automation Status](https://github.com/<USER>/<REPO>/actions/workflows/qa_global_validator.yml/badge.svg)

## Reportes Automáticos
- [Resultados de CI/CD](https://github.com/<USER>/<REPO>/actions)
- [Cobertura de tests (pytest-cov)](https://github.com/<USER>/<REPO>/actions?query=workflow%3AQA+Global+Validator)
	- Para ver cobertura local: `pytest --cov=backend tests/`
	- Puedes integrar [codecov](https://about.codecov.io/) o [coveralls](https://coveralls.io/) para badges de cobertura.




## Resumen Ejecutivo

Lokigi es una plataforma SaaS de inteligencia de negocios locales. Ofrece dashboards, alertas, reportes y automatización de marketing para negocios, consultores y agencias. El modelo es freemium con upgrades premium y funcionalidades avanzadas para usuarios de pago. Integra backend en Python (FastAPI), frontend en Next.js/TypeScript, Supabase y Stripe. El sistema es modular, escalable y fácil de desplegar tanto en local como en la nube.

+### Documentación de Flujos y Procesos
+- [Documentación de Flujos, Modelo de Negocio y Tipos de Usuario](DOCUMENTACION_FLUJOS_NEGOCIO.md)
+- [Flujos de Negocio y Usuario (Premium, Worker, Admin) + Diagramas](README_FLUJOS_NEGOCIO.md)
+- [Retargeting Engine: Automatización de Mensajería y Colas (FastAPI, Supabase, Stripe, SendGrid, Twilio)](backend/RETARGETING_ENGINE_README.md)
+- [Atribución y Prevención de Fraude: Algoritmo, lógica de cookies y comisiones multimoneda](backend/ATTRIBUTION_FRAUD_README.md)
+- [Partner Portal: Affiliate Dashboard, métricas y media kit](frontend/src/app/partner/PARTNER_PORTAL_README.md)
+- [QA: Validador de Flujos de Tiempo y Modales (pytest, Lighthouse)](tests/QA_RETARGETING_TIMEFLOWS_README.md)
# Ejemplo de integración de datos reales en el Partner Portal

```tsx
import AffiliateDashboard from 'frontend/src/app/partner/AffiliateDashboard';
// ...
<AffiliateDashboard
	clicks={afiliado.clicks}
	leads={afiliado.leads}
	commissions={afiliado.comisiones}
	affiliateLink={afiliado.link}
	qrCodeUrl={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(afiliado.link)}`}
	mediaKitLinks={mediaKit}
/>
```

Ver detalles y personalización en [frontend/src/app/partner/PARTNER_PORTAL_README.md](frontend/src/app/partner/PARTNER_PORTAL_README.md)
# Ejemplo de integración frontend/backend para atribución y fraude

```typescript
// Frontend: Al hacer click en un link de afiliado
document.cookie = `lokigi_affiliate_id=${affiliateId}; path=/; max-age=${60*60*24*30}`;

// Backend: Al recibir una venta
from backend.attribution_fraud import atribuir_venta, detectar_fraude, calcular_comisiones
afiliado = atribuir_venta(eventos_clicks, fecha_venta)
alertas = detectar_fraude(afiliado, comprador_id, ip_afiliado, ip_comprador, eventos, fecha_venta)
comisiones = calcular_comisiones(ventas, moneda_afiliado, tasas_cambio)
```

Ver detalles y personalización en [backend/ATTRIBUTION_FRAUD_README.md](backend/ATTRIBUTION_FRAUD_README.md)


---

## Estructura del Proyecto

- **backend/**: Lógica de negocio, API y procesamiento de datos en Python.
- **frontend/**: Aplicación web en Next.js/TypeScript.
- **supabase/**: Funciones y esquemas SQL para la base de datos Supabase.
- **tests/**: Pruebas automatizadas para backend.
- **package.json**: Dependencias y scripts del proyecto.
- **supabase_schema.sql**: Esquema de base de datos.

---

## Instalación y Configuración

### Requisitos
- Node.js >= 18.x
- Python >= 3.10
- PostgreSQL (o Supabase)
- Git

### Variables de Entorno
- Crear un archivo `.env` en `backend/` y `frontend/` con las variables necesarias (ver ejemplos en cada sección).

### Instalación Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # En Windows
pip install -r requirements.txt
```

### Instalación Frontend
```bash
cd frontend
npm install
```

---

## Uso y Ejecución

### Backend
```bash
cd backend
.venv\Scripts\activate
python main.py
```

### Frontend
```bash
cd frontend
npm run dev
```

---

## Manual de Implementación

### Backend
- Estructura modular con archivos para cada funcionalidad.
- Endpoints documentados con docstrings.
- Integración con Stripe y Supabase.
- Pruebas en `tests/`.

### Frontend
- Estructura basada en rutas y componentes.
- Uso de TypeScript y buenas prácticas de React.
- Integración con APIs del backend y Supabase.

### Despliegue
- Usar servicios como Vercel (frontend) y Azure/AWS/Heroku (backend).
- Configurar variables de entorno en el entorno de despliegue.

---

## QA Automation


### Validador Global de Inteligencia

La suite de QA automatizada valida el sentido común, localización y performance de la IA en diferentes culturas y escenarios de negocio.

- Pruebas de Consistencia: Lucro Cesante nunca negativo.
- Pruebas de Localización: Ticket promedio y moneda cambian correctamente entre Brasil y USA.
- Pruebas de Performance: Lighthouse > 95 en Vercel con el mapa de calor.
- Pruebas de Flujos de Tiempo y Modales: Garantiza que los mensajes de retargeting se envíen en el momento correcto y que los modales no degraden la UX ni la performance móvil.

+Ver detalles y ejecución en:
+- [tests/QA_AUTOMATION_README.md](tests/QA_AUTOMATION_README.md)
+- [tests/QA_RETARGETING_TIMEFLOWS_README.md](tests/QA_RETARGETING_TIMEFLOWS_README.md)
+
+### Integración en CI/CD
+El test de flujos de tiempo y modales se ejecuta automáticamente en cada push/pull request:
+
+```yaml
+# .github/workflows/qa_global_validator.yml (fragmento relevante)
+      - name: Run QA Retargeting Timeflows
+        run: pytest tests/test_retargeting_timeflows.py
+      - name: Show QA Retargeting Timeflows README
+        run: cat tests/QA_RETARGETING_TIMEFLOWS_README.md || true
+```
+
+Esto garantiza que los flujos de retargeting y la UX de modales estén siempre validados en el pipeline.

- Mantener actualizado `.gitignore`.
- Documentar funciones y módulos con docstrings y comentarios.
- Usar control de versiones y ramas para nuevas funcionalidades.
- Escribir pruebas automatizadas para nuevas funciones.

---

## Recursos y Enlaces
- [Supabase](https://supabase.com/)
- [Next.js](https://nextjs.org/)
- [Stripe](https://stripe.com/)

---

## Contacto
Para soporte o contribuciones, contactar a los administradores del repositorio.
