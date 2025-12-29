

from fastapi import FastAPI, HTTPException, Query, Body, Response, Request
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pydantic import BaseModel, Field
from typing import Dict, Optional
from .growth_projection import project_growth
from .alert_radar import detect_competitor_anomalies, redactar_alerta_gemini


app = FastAPI()

# Endpoint protegido: /dashboard/premium
from fastapi import Header

@app.get("/dashboard/premium")
def premium_dashboard(x_user_role: str = Header(None)):
    # Solo permite acceso a roles de suscripción
    if x_user_role not in ["PREMIUM", "SUPERUSER"]:
        return Response("Prohibido", status_code=403)
    return {"status": "ok", "message": "Bienvenido al dashboard premium"}

# Modelos y endpoint de alert-radar
class Snapshot(BaseModel):
    name: str
    history: list

class AlertRadarRequest(BaseModel):
    snapshots: list
    country: Optional[str] = "US"
    lang: Optional[str] = "es"

@app.post("/alert-radar")
def alert_radar(data: AlertRadarRequest):
    alerts = detect_competitor_anomalies(data.snapshots, country=data.country)
    # Redactar con Gemini simulado
    insights = [redactar_alerta_gemini(alert, lang=data.lang) for alert in alerts]
    return {"alerts": insights, "raw": alerts}

class GrowthProjectionRequest(BaseModel):
    initial_score: float = Field(..., ge=0, le=100)
    final_score: float = Field(..., ge=0, le=100)
    initial_metrics: Dict[str, float]
    final_metrics: Dict[str, float]
    daily_revenue: float
    currency: str = "USD"

@app.post("/growth/projection")
def growth_projection(data: GrowthProjectionRequest):
    try:
        result = project_growth(
            initial_score=data.initial_score,
            final_score=data.final_score,
            initial_metrics=data.initial_metrics,
            final_metrics=data.final_metrics,
            daily_revenue=data.daily_revenue,
            currency=data.currency
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint GET /impact-report
@app.get("/impact-report")
def get_impact_report(business_id: int = Query(...)):
    # Simulación: en real, consulta a la base de datos y lógica de negocio
    # Aquí se retorna un score fijo para pruebas
    return {
        "business_id": business_id,
        "final_score": 92,
        "details": "Reporte simulado para pruebas QA"
    }

# Endpoint POST /impact-report/pdf
@app.post("/impact-report/pdf")
def generate_impact_report_pdf(payload: dict = Body(...)):
    # Genera un PDF realista con reportlab
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 60, "Lokigi Impact Report")
    c.setFont("Helvetica", 12)
    c.drawString(40, height - 100, f"Nombre: {payload.get('name', 'N/A')}")
    c.drawString(40, height - 120, f"Dirección: {payload.get('address', 'N/A')}")
    c.drawString(40, height - 140, f"Score Final: {payload.get('final_score', 'N/A')}")
    # Simula un bloque de texto largo para probar cortes
    c.setFont("Helvetica", 10)
    # Agrega mucho texto simulado para aumentar el tamaño
    for i in range(30):
        c.drawString(40, height - 180 - i*14, f"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Línea {i+1}.")
    # Simula varios gráficos (rectángulos y líneas)
    for j in range(5):
        y = height - 400 - j*40
        c.setStrokeColorRGB(0.2, 0.8, 0.2)
        c.setFillColorRGB(0.9, 1, 0.9)
        c.rect(40, y, 300, 30, fill=1)
        c.setFont("Helvetica", 9)
        c.drawString(50, y + 10, f"[Radar Chart Simulado {j+1}]")
    # Agrega varias páginas para aumentar el tamaño
    for p in range(20):
        c.showPage()
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, height - 60, f"Página extra de simulación {p+1}")
        c.setFont("Helvetica", 10)
        for i in range(60):
            c.drawString(40, height - 100 - i*12, f"Texto simulado página {p+1}, línea {i+1} Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin nec massa.")
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return Response(content=pdf_bytes, media_type="application/pdf")
# Para correr: uvicorn main:app --reload
