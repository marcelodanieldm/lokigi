"""
Backend MVP - Servicio de SEO Local con FastAPI
Endpoint principal: POST /audit/test
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from audit_schemas import BusinessData, AuditRequest, AuditResponse
from analyzer_service import analyzer
from datetime import datetime

# Crear app FastAPI
app = FastAPI(
    title="SEO Local Analyzer API",
    description="API MVP para análisis de SEO Local con IA",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "SEO Local Analyzer",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "audit": "POST /audit/test",
            "docs": "GET /docs"
        }
    }


@app.post("/audit/test", response_model=AuditResponse)
async def audit_business(request: AuditRequest):
    """
    Endpoint principal de auditoría SEO Local
    
    Recibe datos del negocio y retorna un análisis completo con:
    - Score de salud (0-100)
    - Problema crítico a resolver
    - Impacto económico en dinero perdido
    - Análisis FODA completo
    - Comparación con 3 competidores
    - Plan de acción detallado
    
    El análisis usa un "Consultor de IA" que habla en términos de
    dinero perdido y clientes robados por la competencia.
    """
    try:
        # Ejecutar análisis
        result = analyzer.analyze(
            business=request.business,
            use_ai=request.include_ai_analysis
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en el análisis: {str(e)}"
        )


@app.post("/audit/quick", response_model=dict)
async def quick_audit(business: BusinessData):
    """
    Endpoint simplificado para análisis rápido
    Retorna solo score y problema crítico
    """
    try:
        result = analyzer.analyze(business, use_ai=False)
        
        return {
            "score": result.score,
            "critical_fix": result.critical_fix,
            "economic_impact": result.economic_impact,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


# Ejemplo de uso para testing
@app.get("/audit/example")
async def get_example_request():
    """
    Retorna un ejemplo de request para testing
    """
    return {
        "business": {
            "name": "Restaurante El Sabor Local",
            "rating": 3.8,
            "review_count": 47,
            "has_website": False,
            "is_claimed": False,
            "last_photo_date": "2023-06-15",
            "category": "Restaurante",
            "location": "Madrid Centro"
        },
        "include_ai_analysis": True
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SEO Local Analyzer API...")
    print("📡 API Docs: http://localhost:8000/docs")
    print("🧪 Test endpoint: POST http://localhost:8000/audit/test")
    uvicorn.run(app, host="0.0.0.0", port=8000)
