from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime
from typing import Optional
import os
import json

app = FastAPI(title="Lokigi - Local SEO Auditor")

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


@app.get("/audit/test")
async def audit_test():
    """
    Endpoint de prueba que simula datos de un negocio y genera un reporte
    de auditoría SEO Local usando OpenAI
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
