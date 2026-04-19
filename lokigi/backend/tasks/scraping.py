

from backend.celery_app import celery
from loguru import logger
from backend.models import ReviewSentiment, Competitor
from backend.db import SessionLocal
from celery import chain
import random
import time

@celery.task(name="tasks.scraping.run_scraper")
def run_scraper(url: str):
    logger.info(f"[ScraperWorker] Iniciando scraping para: {url}")
    # Simulación de scraping: genera 3 reseñas dummy
    fake_reviews = [
        "La comida estuvo excelente y el servicio muy atento.",
        "El local estaba sucio y la atención fue lenta.",
        "Precios altos pero la calidad es buena. Volvería por la limpieza."
    ]
    competitor_id = 1  # En real, buscar por URL o mapping
    results = []
    with SessionLocal() as db:
        for text in fake_reviews:
            review = ReviewSentiment(competitor_id=competitor_id, review_text=text, sentiment=0)
            db.add(review)
            db.commit()
            db.refresh(review)
            # Lanza AIWorker para analizar la reseña
            from backend.tasks.ai_insights import run_ai
            ai_result = run_ai.delay({"review_text": text})
            results.append({"review_id": review.id, "ai_task_id": ai_result.id})
            logger.info(f"Scraped & queued AI for review {review.id}")
    logger.success(f"[ScraperWorker] Scraping completado para: {url}")
    return {"url": url, "reviews": results}
