from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse
from backend.db import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models import Competitor, ReviewSentiment
import os
from datetime import datetime
import matplotlib.pyplot as plt
from weasyprint import HTML

router = APIRouter()
REPORTS_DIR = "backend/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

async def get_db():
    async with SessionLocal() as session:
        yield session

def generate_pdf_report(data, filename):
    # Genera gráfico comparativo
    plt.figure(figsize=(6,4))
    names = [d['name'] for d in data]
    sentiments = [d['sentiment'] for d in data]
    plt.bar(names, sentiments, color='skyblue')
    plt.title('Comparativa de Sentimiento')
    plt.ylabel('Sentimiento promedio')
    plt.tight_layout()
    img_path = os.path.join(REPORTS_DIR, 'plot.png')
    plt.savefig(img_path)
    plt.close()
    # HTML para PDF
    html = f"""
    <h1>Reporte Plan Growth</h1>
    <img src='plot.png' width='400'/>
    <ul>
    {''.join([f'<li>{d['name']}: {d['sentiment']:.2f}</li>' for d in data])}
    </ul>
    """
    pdf_path = os.path.join(REPORTS_DIR, filename)
    HTML(string=html, base_url=REPORTS_DIR).write_pdf(pdf_path)
    return pdf_path

@router.get("/report/generate")
async def generate_report(db: AsyncSession = Depends(get_db)):
    competitors = (await db.execute(select(Competitor))).scalars().all()
    data = []
    for c in competitors:
        reviews = (await db.execute(select(ReviewSentiment).where(ReviewSentiment.competitor_id == c.id))).scalars().all()
        avg_sentiment = sum([r.sentiment for r in reviews])/len(reviews) if reviews else 0
        data.append({"name": c.name, "sentiment": avg_sentiment})
    filename = f"growth_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = generate_pdf_report(data, filename)
    return {"report": filename}

@router.get("/report/download/{filename}")
def download_report(filename: str):
    pdf_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(pdf_path):
        return Response(status_code=404, content="Reporte no encontrado")
    return FileResponse(pdf_path, media_type="application/pdf", filename=filename)

@router.get("/report/list")
def list_reports():
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith('.pdf')]
    return {"reports": files}
