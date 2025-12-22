from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
import os
import json

from database import get_db, init_db
from models import Lead, PaymentStatus
from schemas import LeadCreate, LeadResponse, AuditReportSchema, CheckoutResponse
from stripe_service import create_checkout_session, handle_webhook_event
from middleware_i18n import LanguageDetectionMiddleware

# Importar las rutas de pagos y dashboard
from api_payments import router as payments_router
from api_dashboard import router as dashboard_router
from api_auth import router as auth_router
from api_lokigi_score import router as lokigi_score_router
from api_v1 import router as api_v1_router
from api_data_quality import router as data_quality_router
from api_radar import router as radar_router
from api_radar_subscription import router as radar_subscription_router

app = FastAPI(
    title="Lokigi - Local SEO Auditor",
    description="""
    🌎 **API Multilingüe de Presupuesto Cero**
    
    Lokigi es una plataforma de auditoría SEO local que funciona con:
    - ✅ FastAPI + Supabase (PostgreSQL)
    - ✅ Google Gemini AI (capa gratuita)
    - ✅ i18n automático por IP (PT/ES/EN)
    - ✅ Algoritmo Lokigi Score (0-100)
    - ✅ Cálculo de Lucro Cesante
    
    ## 🎯 Endpoint Principal
    
    **POST /api/v1/analyze** - Analiza un negocio local y calcula:
    - Lokigi Score (0-100) con 4 dimensiones
    - Lucro Cesante mensual/anual en USD
    - Problemas críticos detectados
    - Plan de acción priorizado
    
    ## 🌍 Países Soportados
    - 🇦🇷 Argentina
    - 🇧🇷 Brasil
    - 🇲🇽 México
    - 🇨🇴 Colombia
    - 🇨🇱 Chile
    - 🇪🇸 España
    - 🇺🇸 Estados Unidos
    """,
    version="1.0.0",
    contact={
        "name": "Lokigi Team",
        "email": "support@lokigi.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Middleware de detección de idioma (debe ir ANTES de CORS)
app.add_middleware(LanguageDetectionMiddleware)

# Incluir rutas (V1 primero para que aparezca arriba en Swagger)
app.include_router(api_v1_router)
app.include_router(payments_router)
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(lokigi_score_router)
app.include_router(data_quality_router)
app.include_router(radar_router)
app.include_router(radar_subscription_router)

# CORS para el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Detected-Language", "X-Detected-Country"],  # Exponer headers de i18n
)

# Inicializar base de datos al arrancar
@app.on_event("startup")
async def startup_event():
    init_db()

# Configurar cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class BusinessData(BaseModel):
    """Modelo de datos del negocio en Google Maps"""
    nombre: str
    rating: float
    numero_resenas: int
    tiene_sitio_web: bool
    fecha_ultima_foto: str


class FalloCritico(BaseModel):
    """Modelo de un fallo crítico detectado"""
    titulo: str
    descripcion: str
    impacto_economico: str


class AuditReport(BaseModel):
    """Modelo del reporte de auditoría"""
    fallos_criticos: list[FalloCritico]
    score_visibilidad: int


def generar_datos_simulados() -> BusinessData:
    """Simula datos de un negocio real en Google Maps"""
    return BusinessData(
        nombre="Restaurante El Sabor Local",
        rating=3.8,
        numero_resenas=47,
        tiene_sitio_web=False,
        fecha_ultima_foto="2023-08-15"
    )


async def analizar_con_openai(datos_negocio: BusinessData) -> AuditReport:
    """
    Envía los datos del negocio a OpenAI para análisis de SEO Local
    """
    # Construir el mensaje con los datos del negocio
    datos_formateados = f"""
    Nombre: {datos_negocio.nombre}
    Rating: {datos_negocio.rating}/5.0
    Número de reseñas: {datos_negocio.numero_resenas}
    Tiene sitio web: {'Sí' if datos_negocio.tiene_sitio_web else 'No'}
    Fecha de última foto: {datos_negocio.fecha_ultima_foto}
    """
    
    # Prompt del sistema - Consultor SEO Local agresivo
    system_prompt = """Eres un consultor de SEO Local agresivo. Analiza estos datos y genera un reporte JSON con 3 fallos críticos, el impacto económico de no arreglarlos y un score de visibilidad de 1 a 100.

El formato de respuesta DEBE ser un JSON válido con esta estructura exacta:
{
    "fallos_criticos": [
        {
            "titulo": "Título del fallo",
            "descripcion": "Descripción detallada del problema",
            "impacto_economico": "Pérdida estimada mensual en ventas"
        }
    ],
    "score_visibilidad": 45
}

Sé directo, agresivo y enfócate en el impacto económico real. Usa datos y cifras concretas."""
    
    try:
        # Llamada a OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analiza este negocio:\n{datos_formateados}"}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Extraer y parsear la respuesta
        contenido = response.choices[0].message.content
        reporte_dict = json.loads(contenido)
        
        # Validar y crear el modelo
        return AuditReport(**reporte_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al comunicarse con OpenAI: {str(e)}"
        )


@app.get("/")
async def root():
    """Endpoint raíz de bienvenida"""
    return {
        "mensaje": "Bienvenido a Lokigi - Local SEO Auditor",
        "version": "1.0.0",
        "endpoints": ["/audit/test", "/docs"]
    }


@app.post("/api/leads", response_model=LeadResponse)
async def create_lead(lead_data: LeadCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo lead y genera la auditoría
    """
    try:
        # Verificar si el email ya existe
        existing_lead = db.query(Lead).filter(Lead.email == lead_data.email).first()
        if existing_lead:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        
        # Generar datos simulados del negocio
        datos_negocio = BusinessData(
            nombre=lead_data.nombre_negocio,
            rating=3.8,
            numero_resenas=47,
            tiene_sitio_web=False,
            fecha_ultima_foto="2023-08-15"
        )
        
        # Analizar con OpenAI
        reporte = await analizar_con_openai(datos_negocio)
        
        # Determinar si se ofrece el plan express (score < 50)
        oferta_plan = reporte.score_visibilidad < 50
        
        # Crear el lead en la base de datos
        new_lead = Lead(
            email=lead_data.email,
            telefono=lead_data.telefono,
            nombre_negocio=lead_data.nombre_negocio,
            rating=datos_negocio.rating,
            numero_resenas=datos_negocio.numero_resenas,
            tiene_sitio_web=datos_negocio.tiene_sitio_web,
            fecha_ultima_foto=datos_negocio.fecha_ultima_foto,
            score_visibilidad=reporte.score_visibilidad,
            fallos_criticos=[f.model_dump() for f in reporte.fallos_criticos],
            oferta_plan_express=oferta_plan,
            payment_status=PaymentStatus.PENDING
        )
        
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        
        return new_lead
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear lead: {str(e)}"
        )


@app.get("/api/leads/{lead_id}/audit")
async def get_audit_results(lead_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los resultados completos de auditoría de un lead
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    return {
        "success": True,
        "lead": {
            "id": lead.id,
            "email": lead.email,
            "nombre_negocio": lead.nombre_negocio,
        },
        "datos_analizados": {
            "nombre": lead.nombre_negocio,
            "rating": lead.rating,
            "numero_resenas": lead.numero_resenas,
            "tiene_sitio_web": lead.tiene_sitio_web,
            "fecha_ultima_foto": lead.fecha_ultima_foto,
        },
        "reporte": {
            "fallos_criticos": lead.fallos_criticos,
            "score_visibilidad": lead.score_visibilidad,
        },
        "oferta_plan_express": lead.oferta_plan_express,
        "payment_status": lead.payment_status,
        "timestamp": lead.created_at.isoformat()
    }


@app.post("/api/leads/{lead_id}/checkout", response_model=CheckoutResponse)
async def create_checkout(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Crea una sesión de checkout de Stripe para el Plan Express
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    if not lead.oferta_plan_express:
        raise HTTPException(status_code=400, detail="Este lead no califica para el plan express")
    
    if lead.payment_status == PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Ya has pagado por este plan")
    
    try:
        # URLs de éxito y cancelación
        success_url = f"http://localhost:3000/success?lead_id={lead_id}"
        cancel_url = f"http://localhost:3000/audit/{lead_id}"
        
        checkout_data = create_checkout_session(lead, success_url, cancel_url)
        
        # Guardar el session_id en el lead
        lead.stripe_checkout_session_id = checkout_data['session_id']
        db.commit()
        
        return checkout_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear checkout: {str(e)}"
        )


@app.post("/api/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Webhook para recibir eventos de Stripe
    """
    try:
        payload = await request.body()
        result = handle_webhook_event(payload, stripe_signature, db)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit/test")
async def audit_test():
    """
    Endpoint de prueba (DEPRECATED - usar /api/leads)
    """
    try:
        # Generar datos simulados
        datos_negocio = generar_datos_simulados()
        
        # Analizar con OpenAI
        reporte = await analizar_con_openai(datos_negocio)
        
        # Retornar respuesta completa
        return {
            "success": True,
            "datos_analizados": datos_negocio.model_dump(),
            "reporte": reporte.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )


@app.post("/audit/custom")
async def audit_custom(datos: BusinessData):
    """
    Endpoint para auditar datos personalizados de un negocio
    """
    try:
        reporte = await analizar_con_openai(datos)
        
        return {
            "success": True,
            "datos_analizados": datos.model_dump(),
            "reporte": reporte.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
