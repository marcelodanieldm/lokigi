"""
Middleware para FastAPI - Detección automática de idioma por IP
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ip_geolocation import detect_language_from_request_headers, Language


class LanguageDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware que detecta el idioma del usuario automáticamente
    y lo adjunta al request.state
    """
    
    async def dispatch(self, request: Request, call_next):
        # Detectar idioma basado en IP
        headers = dict(request.headers)
        language = detect_language_from_request_headers(headers)
        
        # Adjuntar al request state para que esté disponible en los endpoints
        request.state.language = language
        
        # Continuar con la request
        response = await call_next(request)
        
        # Agregar header de idioma detectado a la respuesta
        response.headers["X-Detected-Language"] = language.value
        
        return response


def get_request_language(request: Request) -> Language:
    """
    Helper para obtener el idioma del request
    
    Usage en endpoints:
        @app.get("/")
        async def endpoint(request: Request):
            language = get_request_language(request)
    """
    return getattr(request.state, "language", Language.ENGLISH)
