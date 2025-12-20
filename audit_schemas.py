from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BusinessData(BaseModel):
    """Datos del negocio para auditoría SEO Local"""
    name: str = Field(..., description="Nombre del negocio")
    rating: float = Field(..., ge=0, le=5, description="Rating de 0 a 5")
    review_count: int = Field(..., ge=0, description="Número de reseñas")
    has_website: bool = Field(..., description="Tiene sitio web activo")
    is_claimed: bool = Field(..., description="Negocio reclamado en Google")
    last_photo_date: str = Field(..., description="Fecha de la última foto (YYYY-MM-DD)")
    
    # Opcional: datos adicionales
    category: Optional[str] = Field(None, description="Categoría del negocio")
    location: Optional[str] = Field(None, description="Ubicación/Ciudad")


class CompetitorData(BaseModel):
    """Datos de un competidor"""
    name: str
    rating: float
    review_count: int
    has_website: bool
    distance_km: float
    estimated_monthly_revenue: str


class FODAAnalysis(BaseModel):
    """Análisis FODA del negocio"""
    fortalezas: List[str] = Field(..., description="Puntos fuertes actuales")
    oportunidades: List[str] = Field(..., description="Oportunidades de mejora")
    debilidades: List[str] = Field(..., description="Puntos débiles críticos")
    amenazas: List[str] = Field(..., description="Amenazas externas")


class AuditResponse(BaseModel):
    """Respuesta completa de la auditoría"""
    score: int = Field(..., ge=0, le=100, description="Score de salud SEO Local")
    critical_fix: str = Field(..., description="El problema más urgente a resolver")
    economic_impact: str = Field(..., description="Dinero/clientes perdidos")
    foda: FODAAnalysis = Field(..., description="Análisis FODA")
    competitors: List[CompetitorData] = Field(..., description="3 competidores cercanos")
    detailed_analysis: str = Field(..., description="Análisis detallado del consultor")
    action_plan: List[str] = Field(..., description="Pasos accionables inmediatos")


class AuditRequest(BaseModel):
    """Request para auditoría"""
    business: BusinessData
    include_ai_analysis: bool = Field(default=True, description="Usar análisis de IA con OpenAI")
