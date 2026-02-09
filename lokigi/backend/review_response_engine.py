"""
Review Response Engine - Backend FastAPI
---------------------------------------
- Endpoint: POST /worker/generate-replies
- Recibe: lote de reseñas, temperatura, tono
- Devuelve: sugerencias generadas por Gemini
- Seguridad: solo WORKER o ADMIN (Supabase)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Literal

# Simulación de autenticación Supabase (reemplazar por lógica real)
def get_current_user_role():
    # Aquí deberías extraer el rol real del usuario autenticado
    # Por ejemplo, desde el JWT de Supabase
    return "WORKER"  # o "ADMIN", "USER", etc.

# --- Modelos ---
class ReviewBatchRequest(BaseModel):
    reviews: List[str]
    temperature: float = 0.7
    tone: Literal["Professional", "Casual", "Grateful"] = "Professional"
    lang: str = "es"

class ReviewBatchResponse(BaseModel):
    suggestions: List[str]

# --- Simulación de integración Gemini (reemplazar por llamada real) ---
def generate_gemini_reply(review: str, tone: str, temperature: float, lang: str) -> str:
    # Aquí deberías llamar a la API real de Gemini
    # Prompt engineering según tono
    if tone == "Professional":
        prefix = {"es": "Respuesta profesional:", "pt": "Resposta profissional:", "en": "Professional reply:"}[lang]
    elif tone == "Casual":
        prefix = {"es": "Respuesta casual:", "pt": "Resposta casual:", "en": "Casual reply:"}[lang]
    else:
        prefix = {"es": "Respuesta agradecida:", "pt": "Resposta agradecida:", "en": "Grateful reply:"}[lang]
    return f"{prefix} Gracias por tu comentario sobre '{review[:30]}...'"

router = APIRouter()

@router.post("/worker/generate-replies", response_model=ReviewBatchResponse)
def generate_replies(
    data: ReviewBatchRequest,
    user_role: str = Depends(get_current_user_role)
):
    if user_role not in ("WORKER", "ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    # Llamada batch a Gemini (simulada)
    suggestions = [
        generate_gemini_reply(r, data.tone, data.temperature, data.lang)
        for r in data.reviews
    ]
    return ReviewBatchResponse(suggestions=suggestions)
