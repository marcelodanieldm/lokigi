from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from backend.db import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models import Competitor, ReviewSentiment
import aiohttp

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

async def get_db():
    async with SessionLocal() as session:
        yield session

async def get_celery_status():
    # Consulta Flower API para estado de workers (puedes ajustar el endpoint)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:5555/api/workers") as resp:
                return await resp.json()
    except Exception:
        return {}

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    competitors = (await db.execute(select(Competitor))).scalars().all()
    alerts = (await db.execute(select(ReviewSentiment).order_by(ReviewSentiment.review_date.desc()).limit(10))).scalars().all()
    celery_status = await get_celery_status()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "competitors": competitors,
        "alerts": alerts,
        "celery_status": celery_status,
    })
