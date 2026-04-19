# Escalabilidad y despliegue avanzado

- Puedes lanzar múltiples instancias de cada worker Celery:
  - `celery -A backend.celery_app:celery worker -Q scraping -n scraper@%h -c 4` (4 procesos)
  - `celery -A backend.celery_app:celery worker -Q ai -n ai@%h -c 4`
- Usa balanceadores (nginx, traefik) para exponer FastAPI en alta disponibilidad.
- Docker Compose soporta escalar servicios:
  - `docker-compose up --scale celery-scraper=3 --scale celery-ai=2`
- Para autoescalado en cloud, usa Kubernetes (Helm charts, HPA) o servicios serverless.
- Configura alertas y monitoreo con Prometheus, Grafana, Sentry, etc.
- Usa Redis Cluster para alta disponibilidad de broker/result backend.
