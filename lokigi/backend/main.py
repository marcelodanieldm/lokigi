from pydantic import BaseModel
from typing import Dict
from growth_projection import project_growth

# --- Endpoint para proyección de crecimiento ---
class GrowthProjectionRequest(BaseModel):
    initial_score: float
    final_score: float
    initial_metrics: Dict[str, float]
    final_metrics: Dict[str, float]
    daily_revenue: float
    currency: str = "USD"

@app.post("/growth/projection")
def growth_projection(data: GrowthProjectionRequest):
    """
    Calcula la proyección de crecimiento y dataset para radar chart.
    """
    return project_growth(
        initial_score=data.initial_score,
        final_score=data.final_score,
        initial_metrics=data.initial_metrics,
        final_metrics=data.final_metrics,
        daily_revenue=data.daily_revenue,
        currency=data.currency
    )
# Integración del Review Response Engine
from review_response_engine import router as review_response_router

app.include_router(review_response_router)
from fastapi import APIRouter

from pydantic import BaseModel
from typing import List

# --- Modelo para el endpoint de análisis de sentimiento y SEO ---
class ReviewAnalysisRequest(BaseModel):
    reviews: List[str]
    lang: str = 'es'  # 'es', 'pt', 'en'

class ReviewAnalysisResponse(BaseModel):
    keywords: List[str]
    sentiments: dict
    prompt: str

@app.post("/seo-sentiment-analysis", response_model=ReviewAnalysisResponse)
def seo_sentiment_analysis(data: ReviewAnalysisRequest):
    """
    Analiza un corpus de reseñas: extrae palabras clave, clasifica sentimiento y genera prompt SEO para IA.
    """
    keywords = extract_keywords(data.reviews)
    sentiments = sentiment_analysis(data.reviews, data.lang)
    prompt = build_gemini_prompt(keywords, data.lang)
    return ReviewAnalysisResponse(
        keywords=keywords,
        sentiments={k: len(v) for k, v in sentiments.items()},
        prompt=prompt
    )
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sentiment_seo_reviews import extract_keywords, sentiment_analysis, build_gemini_prompt


from fastapi import FastAPI, HTTPException, Query, Body, Response, Request, BackgroundTasks
import uuid
import os
from supabase import create_client, Client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
# --- Auditoría asíncrona con streaming y cacheo ---
class AsyncAuditRequest(BaseModel):
    score: float
    rubro: str = "Peluquería"
    competencia: str = "3 locales en un radio de 1km con 4.5 estrellas"
    fallo: str = "No tiene fotos de los trabajos realizados (Social Proof)"
    pais: str = "AR"
    lang: str = "es"
    client: Business
    competitors: List[Business]
    locale: str = "es"

def cache_audit_result(audit_id, result):
    if supabase:
        supabase.table("audit_cache").insert({"audit_id": audit_id, "result": result}).execute()

def get_cached_audit(audit_id):
    if supabase:
        res = supabase.table("audit_cache").select("result").eq("audit_id", audit_id).single().execute()
        if res.data:
            return res.data["result"]
    return None

def async_audit_task(audit_id, data: AsyncAuditRequest):
    # IA audit
    contexto = {
        "rubro": data.rubro,
        "competencia": data.competencia,
        "fallo": data.fallo,
        "pais": data.pais,
        "lang": data.lang
    }
    alert = {"alert": f"Score actual: {data.score}. Diagnóstico AI requerido."}
    ai_result = redactar_alerta_gemini(alert, lang=data.lang, contexto=contexto)
    # Dominance
    client = data.client.dict()
    competitors = [c.dict() for c in data.competitors]
    dom_result = dominance_index(client, competitors, locale=data.locale)
    # Cachear resultado
    result = {"ai": ai_result, "dominance": dom_result}
    cache_audit_result(audit_id, result)

@app.post("/audit")
def audit_async(data: AsyncAuditRequest, background_tasks: BackgroundTasks):
    """
    Inicia auditoría asíncrona. Devuelve audit_id inmediato (<500ms).
    El análisis IA y Dominance se procesa en background y se cachea en Supabase.
    """
    audit_id = str(uuid.uuid4())
    # Si ya existe en cache, no relanzar
    if get_cached_audit(audit_id):
        return {"audit_id": audit_id}
    background_tasks.add_task(async_audit_task, audit_id, data)
    return {"audit_id": audit_id}

@app.get("/audit/result/{audit_id}")
def get_audit_result(audit_id: str):
    """
    Devuelve el resultado de la auditoría si está listo.
    """
    result = get_cached_audit(audit_id)
    if result:
        return result
    return {"status": "processing"}
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pydantic import BaseModel, Field
from typing import Dict, Optional
from .growth_projection import project_growth
from .alert_radar import detect_competitor_anomalies, redactar_alerta_gemini
from .dominance_index import dominance_index

# Dominance Index API
from typing import List

class Business(BaseModel):
        lat: float
        lon: float
        rating: float
        review_count: int
        name: str = "Cliente"

class DominanceRequest(BaseModel):
        client: Business
        competitors: List[Business]
        locale: str = "es"

@app.post("/dominance-index")
def dominance_index_api(data: DominanceRequest):
        """
        Calcula el Dominance Index, Competidor Amenaza y heatmap de rivalidad.
        Body ejemplo:
        {
            "client": {"lat": 38.72, "lon": -9.13, "rating": 4.8, "review_count": 120, "name": "Mi Negocio"},
            "competitors": [
                {"lat": 38.723, "lon": -9.14, "rating": 4.7, "review_count": 200, "name": "Barberia Lisboa"},
                ...
            ],
            "locale": "pt"
        }
        """
        client = data.client.dict()
        competitors = [c.dict() for c in data.competitors]
        result = dominance_index(client, competitors, locale=data.locale)
        return result


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

        @app.post("/audit/gemini_prompt", status_code=status.HTTP_200_OK)
        def audit_gemini_prompt(data: GeminiAuditRequest) -> Any:
            """
            Endpoint para auditar un negocio local usando Gemini y prompt engineering avanzado.
            Devuelve un JSON con QuickWin, StrategicGap y TechnicalFix.
            """
            contexto = {
                "rubro": data.rubro,
                "competencia": data.competencia,
                "fallo": data.fallo,
                "pais": data.pais,
                "lang": data.lang
            }
            # El score puede usarse para enriquecer el contexto si se desea
            alert = {"alert": f"Score actual: {data.score}. Diagnóstico AI requerido."}
            result = redactar_alerta_gemini(alert, lang=data.lang, contexto=contexto)
            return result

        class GeminiAuditRequest(BaseModel):
            score: float
            rubro: str = "Peluquería"
            competencia: str = "3 locales en un radio de 1km con 4.5 estrellas"
            fallo: str = "No tiene fotos de los trabajos realizados (Social Proof)"
            pais: str = "AR"
            lang: str = "es"

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

# Endpoint para generación y automatización de PDF de éxito
from utils.success_pdf import generate_success_certificate_pdf
from utils.supabase_pdf import upload_pdf_to_supabase
from utils.email_sendgrid import send_success_email
import uuid

class OrderRequest(BaseModel):
    user_email: str
    business_id: str = None
    lang: str = "es"  # 'es', 'pt', 'en'
    name: str = ""
    address: str = ""
    final_score: float = 0
    improvements: list = []
    photos: list = []
    ranking: list = []
    radar_labels: list = []
    radar_before: list = []
    radar_after: list = []

@app.post("/order")
def create_order_and_report(data: OrderRequest):
    # 1. Generar PDF multilingüe
    pdf_bytes = generate_success_certificate_pdf(data.dict(), lang=data.lang)
    # 2. Subir a Supabase Storage
    order_id = str(uuid.uuid4())
    filename = f"{order_id}.pdf"
    public_url = upload_pdf_to_supabase(pdf_bytes, filename)
    if not public_url:
        raise HTTPException(status_code=500, detail="Error al subir PDF a Supabase")
    # 3. Guardar en tabla orders
    if supabase:
        supabase.table("orders").insert({
            "id": order_id,
            "user_email": data.user_email,
            "business_id": data.business_id,
            "report_url": public_url,
            "lang": data.lang
        }).execute()
    # 4. Enviar email con enlace
    email_ok = send_success_email(data.user_email, public_url, lang=data.lang)
    return {"order_id": order_id, "report_url": public_url, "email_sent": email_ok}
