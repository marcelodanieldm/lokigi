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

Lokigi es una plataforma que integra un backend en Python y un frontend en Next.js/TypeScript para la gestión, análisis y visualización de datos, con integración a servicios como Supabase y Stripe. El sistema está diseñado para ser modular, escalable y fácil de desplegar tanto en entornos locales como en la nube.

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

Ver detalles y ejecución en [tests/QA_AUTOMATION_README.md](tests/QA_AUTOMATION_README.md).

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
