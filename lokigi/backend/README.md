# Ejemplo de README para Lokigi Backend

## Despliegue local

```bash
git clone ...
cd lokigi
cp backend/.env.example backend/.env
# Docker Compose
sudo docker-compose up --build
# O manual
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
# Workers
celery -A backend.celery_app:celery worker -Q scraping -n scraper@%h
celery -A backend.celery_app:celery worker -Q ai -n ai@%h
```

## Endpoints principales
- `POST /start-scraping`  
- `POST /process-insights`  
- `GET /health`  
- `GET /health/redis`  

## Monitoreo y logs
- Flower: http://localhost:5555
- Logs: logs/api.log

## Pruebas
```bash
pytest backend/test_api.py
pytest backend/test_tasks.py
```


## Observabilidad avanzada
- Prometheus: `/metrics` para métricas de FastAPI (puedes conectar Prometheus y Grafana)
- Sentry: agrega en main.py y celery_app.py:
	```python
	import sentry_sdk
	sentry_sdk.init(dsn="TU_SENTRY_DSN")
	```

## Troubleshooting
- Verifica Redis y variables de entorno
- Revisa logs y estado de workers

---

**Para producción:** usa systemd o PM2, configura variables sensibles y usa imágenes Docker seguras.

## Ejemplo de uso de la API
```bash
# Lanzar scraping (esto guarda reseñas y lanza AI automáticamente)
curl -X POST http://localhost:8000/start-scraping -H "Content-Type: application/json" -d '{"url": "https://example.com"}'
# Consultar competidores
curl http://localhost:8000/competitors
# Health
curl http://localhost:8000/health
# Health Redis
curl http://localhost:8000/health/redis
# Métricas Prometheus
curl http://localhost:8000/metrics
```


## Plan Growth: Backend Inteligente y Dashboard

### Arquitectura principal
- **FastAPI**: API principal, endpoints y dashboard SSR (Jinja2 + Tailwind CSS).
- **Celery + Redis**: Orquestación de tareas asíncronas (scraping, AI).
- **SQLAlchemy + Alembic**: Modelos ORM y migraciones para PostgreSQL.
- **Playwright Python**: Scraping robusto de Google Maps (reseñas y Google Posts).
- **Ollama/Llama 3**: Análisis de sentimiento, entidades y brechas competitivas en reseñas.
- **WeasyPrint + Matplotlib**: Generación de reportes PDF con visualizaciones comparativas.
- **Prometheus, Flower, Loguru**: Observabilidad, monitoreo y logs estructurados.

### Endpoints principales
- `POST /start-scraping` — Lanza scraping, guarda reseñas y ejecuta AI automáticamente.
- `GET /competitors` — Lista competidores y cliente para comparativas.
- `GET /dashboard` — Dashboard SSR: Radar de Competencia, Alertas Inteligentes, estado de workers Celery.
- `GET /report/generate` — Genera un reporte PDF comparativo y lo guarda localmente.
- `GET /report/list` — Lista reportes PDF históricos.
- `GET /report/download/{filename}` — Descarga un reporte PDF generado.

### Flujo automatizado
1. `/start-scraping` ejecuta MapsScraper (Playwright) para las 5 URLs de la competencia.
2. Se extraen reseñas y Google Posts, que se guardan en la base de datos.
3. Por cada reseña, el AIWorker (Ollama/Llama 3) analiza sentimiento, entidades y brechas competitivas.
4. Los resultados se almacenan y visualizan en el dashboard y reportes.
5. El dashboard SSR muestra radar de competencia, alertas y estado de workers en tiempo real.
6. El usuario puede generar y descargar reportes PDF con comparativas visuales.

### Pruebas y monitoreo
- Ejecuta `pytest backend/test_ai_insights.py` para validar el análisis AI.
- Flower: http://localhost:5555 para monitoreo de workers.
- Prometheus: `/metrics` para métricas de FastAPI.
- Logs estructurados en `logs/api.log`.

### Ejemplo de uso rápido
```bash
# Lanzar scraping y AI
curl -X POST http://localhost:8000/start-scraping -H "Content-Type: application/json" -d '{"url": "https://maps.google.com/...?cid=..."}'
# Dashboard SSR
http://localhost:8000/dashboard
# Generar y descargar PDF
curl http://localhost:8000/report/generate
curl http://localhost:8000/report/list
curl -O http://localhost:8000/report/download/growth_report_YYYYMMDD_HHMMSS.pdf
```

---

**Para producción:** usa systemd o PM2, configura variables sensibles y usa imágenes Docker seguras. Consulta la documentación de cada componente para despliegue avanzado.
