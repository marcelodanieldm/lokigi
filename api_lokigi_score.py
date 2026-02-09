"""
API Endpoint para Lokigi Score Algorithm
Permite a Workers pegar datos manuales de Google Maps
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from lokigi_score_algorithm import (
    LokigiScoreCalculator,
    ManualScrapedData,
    Country,
    LokigiScoreResult,
    quick_analyze_from_text
)
from models import User, Lead
from auth import get_current_user

router = APIRouter(prefix="/api/lokigi-score", tags=["Lokigi Score"])


class ManualDataInput(BaseModel):
    """Datos que el Worker pega manualmente desde Google Maps"""
    business_name: str = Field(..., description="Nombre del negocio")
    address: str = Field(..., description="Dirección completa")
    phone: str = Field(default="", description="Teléfono")
    website: str = Field(default="", description="Sitio web")
    
    # Métricas visibles en GMB
    rating: str = Field(default="0", description="Rating (ej: '4.5')")
    reviews: str = Field(default="0", description="Reseñas (ej: '230 reseñas')")
    
    # Estado del negocio
    claimed_text: str = Field(default="", description="Texto indicando si está reclamado")
    verified_badge: bool = Field(default=False, description="Tiene badge de verificado")
    
    # Categorías
    primary_category: str = Field(default="", description="Categoría principal")
    additional_categories: str = Field(default="", description="Categorías adicionales (separadas por coma)")
    
    # Fotos
    photo_count: str = Field(default="0", description="Cantidad de fotos")
    last_photo_date: str = Field(default="", description="Última foto (ej: 'hace 2 semanas')")
    
    # Horarios
    business_hours: str = Field(default="", description="Horarios de atención")
    
    # Ubicación
    country_code: str = Field(default="AR", description="Código país: AR, BR o US")
    city: str = Field(default="", description="Ciudad")
    
    # Metadata
    lead_email: Optional[str] = Field(None, description="Email del lead si existe")


class LokigiScoreResponse(BaseModel):
    """Respuesta completa del análisis"""
    total_score: int
    score_label: str  # "Excelente", "Bueno", "Regular", "Crítico"
    dimension_scores: dict
    
    # Lucro cesante
    lucro_cesante_mensual_usd: float
    lucro_cesante_anual_usd: float
    clientes_perdidos_mes: int
    
    # Posicionamiento
    ranking_position_estimated: int
    ranking_improvement_potential: int
    
    # Diagnóstico
    critical_issues: List[str]
    recommendations: List[str]
    
    # Metadata
    analyzed_at: str
    country: str


@router.post("/analyze-manual", response_model=LokigiScoreResponse)
async def analyze_manual_data(
    data: ManualDataInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analiza datos pegados manualmente por un Worker desde Google Maps
    
    Workflow:
    1. Worker copia datos de un perfil de Google Maps
    2. Worker pega los datos en el formulario
    3. Sistema calcula Lokigi Score + Lucro Cesante
    4. Se guarda el análisis en el Lead correspondiente
    """
    
    try:
        # Usar la función helper rápida
        result: LokigiScoreResult = quick_analyze_from_text(
            business_name=data.business_name,
            address=data.address,
            phone=data.phone,
            rating=data.rating,
            reviews=data.reviews,
            claimed_text=data.claimed_text,
            category=data.primary_category,
            photos_count=data.photo_count,
            last_photo=data.last_photo_date,
            country_code=data.country_code,
            city=data.city
        )
        
        # Determinar label del score
        score_label = _get_score_label(result.total_score)
        
        # Si hay email del lead, actualizar sus datos
        if data.lead_email:
            lead = db.query(Lead).filter(Lead.email == data.lead_email).first()
            if lead:
                # Actualizar lead con el nuevo análisis
                lead.score_visibilidad = result.total_score
                lead.audit_data = {
                    "lokigi_score": result.total_score,
                    "dimension_scores": result.dimension_scores,
                    "lucro_cesante_mensual": result.lucro_cesante_mensual,
                    "lucro_cesante_anual": result.lucro_cesante_anual,
                    "clientes_perdidos_mes": result.clientes_perdidos_mes,
                    "ranking_position": result.ranking_position_estimated,
                    "analyzed_at": datetime.now().isoformat(),
                    "country": data.country_code,
                    "manual_data": data.dict()
                }
                lead.fallos_criticos = [
                    {"titulo": issue, "impacto": "alto"} 
                    for issue in result.critical_issues
                ]
                db.commit()
        
        return LokigiScoreResponse(
            total_score=result.total_score,
            score_label=score_label,
            dimension_scores=result.dimension_scores,
            lucro_cesante_mensual_usd=result.lucro_cesante_mensual,
            lucro_cesante_anual_usd=result.lucro_cesante_anual,
            clientes_perdidos_mes=result.clientes_perdidos_mes,
            ranking_position_estimated=result.ranking_position_estimated,
            ranking_improvement_potential=result.ranking_improvement_potential,
            critical_issues=result.critical_issues,
            recommendations=result.recommendations,
            analyzed_at=datetime.now().isoformat(),
            country=data.country_code
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar: {str(e)}")


@router.post("/quick-analyze", response_model=LokigiScoreResponse)
async def quick_analyze(
    data: ManualDataInput
):
    """
    Análisis rápido SIN autenticación (para demos o landing page)
    """
    
    try:
        result: LokigiScoreResult = quick_analyze_from_text(
            business_name=data.business_name,
            address=data.address,
            phone=data.phone,
            rating=data.rating,
            reviews=data.reviews,
            claimed_text=data.claimed_text,
            category=data.primary_category,
            photos_count=data.photo_count,
            last_photo=data.last_photo_date,
            country_code=data.country_code,
            city=data.city
        )
        
        score_label = _get_score_label(result.total_score)
        
        return LokigiScoreResponse(
            total_score=result.total_score,
            score_label=score_label,
            dimension_scores=result.dimension_scores,
            lucro_cesante_mensual_usd=result.lucro_cesante_mensual,
            lucro_cesante_anual_usd=result.lucro_cesante_anual,
            clientes_perdidos_mes=result.clientes_perdidos_mes,
            ranking_position_estimated=result.ranking_position_estimated,
            ranking_improvement_potential=result.ranking_improvement_potential,
            critical_issues=result.critical_issues,
            recommendations=result.recommendations,
            analyzed_at=datetime.now().isoformat(),
            country=data.country_code
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar: {str(e)}")


@router.get("/search-volumes/{country_code}")
async def get_search_volumes(country_code: str):
    """
    Retorna los volúmenes de búsqueda por categoría para un país
    """
    country_map = {
        "AR": Country.ARGENTINA,
        "BR": Country.BRASIL,
        "US": Country.EEUU
    }
    
    country = country_map.get(country_code.upper())
    if not country:
        raise HTTPException(status_code=400, detail="País no soportado")
    
    calculator = LokigiScoreCalculator()
    volumes = calculator.SEARCH_VOLUMES.get(country, {})
    
    return {
        "country": country_code,
        "search_volumes": volumes,
        "average_customer_value_usd": calculator.AVERAGE_CUSTOMER_VALUE[country]
    }


def _get_score_label(score: int) -> str:
    """Convierte score numérico en label descriptivo"""
    if score >= 85:
        return "🌟 Excelente"
    elif score >= 70:
        return "✅ Bueno"
    elif score >= 50:
        return "⚠️ Regular"
    elif score >= 30:
        return "🔴 Crítico"
    else:
        return "🚨 Emergencia"
