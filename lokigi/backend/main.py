
from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.celery_app import celery
from backend.health import router as health_router
from backend.prometheus_integration import setup_prometheus
from loguru import logger
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.db import SessionLocal
from backend.models import Competitor, ReviewSentiment, KeywordRanking
from backend.dashboard_router import router as dashboard_router
from backend.report_router import router as report_router



logger.add("logs/api.log", rotation="1 week", retention="4 weeks", level="INFO")
app = FastAPI()
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(report_router)
setup_prometheus(app)

async def get_db():
    async with SessionLocal() as session:
        yield session
from backend.models import Competitor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

@app.get("/competitors")
async def list_competitors(db: AsyncSession = Depends(get_db)):
    """Devuelve todos los competidores y el cliente, con métricas básicas."""
    result = await db.execute(select(Competitor))
    competitors = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "is_client": bool(c.is_client),
        }
        for c in competitors
    ]

class ScrapeRequest(BaseModel):
    url: str

class InsightRequest(BaseModel):
    data: dict


@app.post("/start-scraping")
def start_scraping(req: ScrapeRequest):
    logger.info(f"Scraping requested for url={req.url}")
    celery.send_task("tasks.scraping.run_scraper", args=[req.url], queue="scraping")
    return {"status": "scraping started"}


@app.post("/process-insights")
def process_insights(req: InsightRequest):
    logger.info(f"AI processing requested for data={req.data}")
    celery.send_task("tasks.ai_insights.run_ai", args=[req.data], queue="ai")
    return {"status": "ai processing started"}


@app.get("/health")
def health():
    logger.info("Healthcheck called")
    return {"status": "ok"}
