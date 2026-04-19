from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery = Celery(
    "lokigi",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["tasks.scraping", "tasks.ai_insights"]
)

celery.conf.task_routes = {
    "tasks.scraping.*": {"queue": "scraping"},
    "tasks.ai_insights.*": {"queue": "ai"},
}
