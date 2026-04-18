"""
API V1 - Core Multilingüe
Endpoint principal para análisis de negocios con Lokigi Score

Cumple con especificaciones del equipo de Data:
- i18n automático por IP (PT/ES/EN)
- Validación de Lead antes de entregar análisis
- Algoritmo Lokigi Score integrado
- Respuesta JSON con score, lucro cesante y recomendaciones
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Lead
from lokigi_score_algorithm import (
    quick_analyze_from_text,
    Country,
    LokigiScoreResult
)
from ip_geolocation import IPGeolocationService
from i18n_service import I18nService

router = APIRouter(prefix="/api/v1", tags=["Core API V1"])

# Instanciar servicios
geo_service = IPGeolocationService()
i18n_service = I18nService()


# ========== SCHEMAS ==========

class BusinessAnalysisRequest(BaseModel):
    """
    Datos del negocio a analizar (scraping manual o automático)
    """
    # Datos del Lead (REQUERIDOS para validación)
    lead_email: EmailStr = Field(..., description="Email del lead que solicita análisis")
    lead_whatsapp: Optional[str] = Field(None, description="WhatsApp del lead (opcional)")
    
    # Datos del negocio
    nombre_negocio: str = Field(..., description="Nombre del negocio en Google Maps")
    direccion: str = Field(..., description="Dirección completa")
    telefono: str = Field(default="", description="Teléfono del negocio")
    sitio_web: Optional[str] = Field(None, description="URL del sitio web")
    
    # Métricas de Google Maps
    rating: str = Field(default="0", description="Rating (ej: '4.5' o '4.5 estrellas')")
    numero_resenas: str = Field(default="0", description="Reseñas (ej: '230' o '230 reseñas')")
    
    # Estado de verificación
    texto_reclamado: str = Field(default="", description="Texto que indica si está reclamado")
    badge_verificado: bool = Field(default=False, description="Tiene badge de verificación")
    
    # Categorías
    categoria_principal: str = Field(..., description="Categoría principal (ej: 'Restaurante')")
    categorias_adicionales: str = Field(default="", description="Categorías adicionales separadas por coma")
    
    # Fotos
    cantidad_fotos: str = Field(default="0", description="Cantidad de fotos")
    ultima_foto: str = Field(default="", description="Cuándo se subió la última foto")
    
    # Horarios
    horarios: str = Field(default="", description="Horarios de atención")
    
    # Ubicación (se detecta automáticamente por IP si no se provee)
    codigo_pais: Optional[str] = Field(None, description="Código país: AR, BR, US (auto si es None)")
    ciudad: str = Field(default="", description="Ciudad")


class DimensionScore(BaseModel):
    """Score de una dimensión del algoritmo"""
    nombre: str
    puntos: int
    maximo: int
    porcentaje: int


class BusinessAnalysisResponse(BaseModel):
    """
    Respuesta completa del análisis Lokigi
    """
    # Metadata
    success: bool = True
    analyzed_at: str
    language: str  # PT, ES o EN
    country: str  # BR, AR, US, etc.
    
    # Lokigi Score
    lokigi_score: int = Field(..., description="Score total 0-100")
    score_label: str = Field(..., description="Etiqueta del score")
    
    # Scores por dimensión
    dimensions: List[DimensionScore]
    
    # Lucro Cesante
    lucro_cesante: Dict = Field(..., description="Pérdidas económicas estimadas")
    
    # Diagnóstico
    problemas_criticos: List[str] = Field(..., description="Problemas urgentes detectados")
    recomendaciones: List[str] = Field(..., description="Plan de acción priorizado")
    
    # Posicionamiento
    posicion_estimada: int
    potencial_mejora_posiciones: int
    
    # Lead info (confirmación de guardado)
    lead_id: int
    lead_email: str


# ========== HELPERS ==========

def _validate_lead_exists(email: str, db: Session) -> Lead:
    """
    Valida que el Lead existe en la base de datos
    Si no existe, lo crea automáticamente
    
    REQUERIMIENTO DEL EQUIPO DE DATA:
    "Antes de entregar el análisis completo, el sistema debe validar 
    que el Lead ha sido guardado en Supabase"
    """
    lead = db.query(Lead).filter(Lead.email == email).first()
    
    if not lead:
        # Auto-crear el lead si no existe
        lead = Lead(
            email=email,
            telefono="",
            nombre_negocio="",
            pais="",
            created_at=datetime.utcnow()
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
    
    return lead


def _detect_country_code(request: Request, provided_code: Optional[str]) -> str:
    """
    Detecta código de país por IP o usa el provisto
    """
    if provided_code:
        return provided_code.upper()
    
    # Detectar por IP
    ip = geo_service.get_client_ip_from_headers(dict(request.headers))
    country = geo_service.detect_country_from_ip(ip)
    
    # Mapear Country enum a código
    country_map = {
        "brasil": "BR",
        "argentina": "AR",
        "mexico": "MX",
        "colombia": "CO",
        "chile": "CL",
        "espana": "ES",
        "estados_unidos": "US"
    }
    
    return country_map.get(country.value, "AR")


def _get_score_label(score: int, language: str) -> str:
    """Obtiene etiqueta del score según idioma"""
    if score >= 85:
        labels = {"PT": "Excelente", "ES": "Excelente", "EN": "Excellent"}
    elif score >= 70:
        labels = {"PT": "Bom", "ES": "Bueno", "EN": "Good"}
    elif score >= 50:
        labels = {"PT": "Regular", "ES": "Regular", "EN": "Fair"}
    else:
        labels = {"PT": "Crítico", "ES": "Crítico", "EN": "Critical"}
    
    return labels.get(language, labels["EN"])


def _map_country_code_to_enum(code: str) -> Country:
    """Mapea código de país a Country enum"""
    mapping = {
        "BR": Country.BRASIL,
        "AR": Country.ARGENTINA,
        "MX": Country.ARGENTINA,  # Usamos AR como proxy
        "CO": Country.ARGENTINA,
        "CL": Country.ARGENTINA,
        "ES": Country.ARGENTINA,
        "US": Country.EEUU
    }
    return mapping.get(code, Country.ARGENTINA)


# ========== ENDPOINT PRINCIPAL ==========

@router.post("/analyze", response_model=BusinessAnalysisResponse)
async def analyze_business(
    data: BusinessAnalysisRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    🎯 ENDPOINT PRINCIPAL DEL CORE API MULTILINGÜE
    
    **Funcionalidad:**
    1. Detecta idioma del usuario por IP (PT/ES/EN)
    2. Valida que el Lead existe en Supabase
    3. Ejecuta algoritmo Lokigi Score (0-100)
    4. Calcula Lucro Cesante (pérdida económica)
    5. Genera recomendaciones en el idioma del usuario
    
    **Requerimientos cumplidos:**
    - ✅ i18n automático por IP
    - ✅ Validación de Lead antes de análisis
    - ✅ Algoritmo de Data Team integrado
    - ✅ Respuesta JSON estructurada
    - ✅ Zero-budget (Gemini API gratuita)
    
    **Ejemplo de uso:**
    ```json
    {
      "lead_email": "dueno@pizzeria.com",
      "lead_whatsapp": "+5491123456789",
      "nombre_negocio": "Pizzería El Rincón",
      "direccion": "Av. Corrientes 1234, Buenos Aires",
      "telefono": "+5491145678901",
      "rating": "3.8",
      "numero_resenas": "47",
      "categoria_principal": "Restaurante",
      "cantidad_fotos": "12"
    }
    ```
    
    **Respuesta:**
    - Lokigi Score: 0-100
    - Lucro cesante mensual y anual en USD
    - Problemas críticos detectados
    - Plan de acción priorizado
    """
    
    try:
        # 1. VALIDAR LEAD (Requerimiento del equipo de Data)
        lead = _validate_lead_exists(data.lead_email, db)
        
        # Actualizar datos del lead si se proveen
        if data.lead_whatsapp:
            lead.telefono = data.lead_whatsapp
        if data.nombre_negocio:
            lead.nombre_negocio = data.nombre_negocio
        
        # 2. DETECTAR PAÍS E IDIOMA
        country_code = _detect_country_code(request, data.codigo_pais)
        country_enum = _map_country_code_to_enum(country_code)
        
        # Obtener idioma desde el middleware (ya detectado por IP)
        language = getattr(request.state, 'language', 'ES')
        
        # Actualizar país del lead
        lead.pais = country_code
        db.commit()
        
        # 3. EJECUTAR ALGORITMO LOKIGI SCORE
        result: LokigiScoreResult = quick_analyze_from_text(
            business_name=data.nombre_negocio,
            address=data.direccion,
            phone=data.telefono,
            rating=data.rating,
            reviews=data.numero_resenas,
            claimed_text=data.texto_reclamado,
            category=data.categoria_principal,
            photos_count=data.cantidad_fotos,
            last_photo=data.ultima_foto,
            country_code=country_code,
            city=data.ciudad
        )
        
        # 4. CONSTRUIR RESPUESTA EN FORMATO V1
        
        # Dimensions con nuevas proporciones (40/25/20/15)
        dimensions = []
        for dim_name, score in result.dimension_scores.items():
            max_points = {
                "Propiedad": 40,
                "Reputación": 25,
                "Contenido Visual": 20,
                "Presencia Digital": 15
            }.get(dim_name, 20)
            
            dimensions.append(DimensionScore(
                nombre=dim_name,
                puntos=score,
                maximo=max_points,
                porcentaje=int((score / max_points) * 100)
            ))
        
        # Lucro cesante
        lucro_data = {
            "mensual_usd": result.lucro_cesante_mensual,
            "anual_usd": result.lucro_cesante_anual,
            "clientes_perdidos_mes": result.clientes_perdidos_mes,
            "moneda": "USD",
            "descripcion": f"Pérdida estimada por no estar en posición #1 en Google Maps"
        }
        
        # Score label
        score_label = _get_score_label(result.total_score, language)
        
        # 5. GUARDAR SCORE EN EL LEAD
        lead.score_visibilidad = result.total_score
        db.commit()
        
        # 6. RESPUESTA FINAL
        return BusinessAnalysisResponse(
            analyzed_at=datetime.utcnow().isoformat(),
            language=language,
            country=country_code,
            lokigi_score=result.total_score,
            score_label=score_label,
            dimensions=dimensions,
            lucro_cesante=lucro_data,
            problemas_criticos=result.critical_issues,
            recomendaciones=result.recommendations,
            posicion_estimada=result.ranking_position_estimated,
            potencial_mejora_posiciones=result.ranking_improvement_potential,
            lead_id=lead.id,
            lead_email=lead.email
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al analizar negocio: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check del API V1
    """
    return {
        "status": "healthy",
        "api_version": "v1",
        "features": [
            "i18n automático (PT/ES/EN)",
            "Lokigi Score Algorithm",
            "Lucro Cesante calculation",
            "Lead validation",
            "Zero-budget (Gemini API gratuita)"
        ],
        "supported_countries": ["AR", "BR", "MX", "CO", "CL", "ES", "US"]
    }
