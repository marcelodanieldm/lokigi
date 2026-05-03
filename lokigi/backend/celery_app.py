from celery import Celery
from celery.schedules import crontab
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery = Celery(
    "lokigi",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "tasks.scraping",
        "tasks.ai_insights",
        "tasks.review_processing",
        "tasks.growth",
        "tasks.local_scout",
    ]
)

celery.conf.task_routes = {
    "tasks.scraping.*": {"queue": "scraping"},
    "tasks.growth.*": {"queue": "scraping"},
    "tasks.local_scout.*": {"queue": "scraping"},
    "tasks.ai_insights.*": {"queue": "ai"},
    "tasks.review_processing.process_reviews": {"queue": "process_reviews"},
    "tasks.review_processing.*": {"queue": "reviews"},
}

# ── Beat schedule ─────────────────────────────────────────────────────────────
celery.conf.beat_schedule = {
    # Local Scout: scrape competitor URLs every 48 h (runs at 03:00 UTC Mon & Thu)
    "local-scout-48h": {
        "task": "tasks.local_scout.run_local_scout_all_users",
        "schedule": crontab(hour=3, minute=0, day_of_week="1,4"),  # Mon + Thu
    },
}
