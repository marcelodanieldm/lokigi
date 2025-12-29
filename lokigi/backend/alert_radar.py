# backend/alert_radar.py
"""
Motor de Detección de Anomalías Competitivas para Lokigi
"""
import datetime
from typing import List, Dict, Any

def detect_competitor_anomalies(snapshots: List[Dict[str, Any]], country: str = "US") -> List[Dict[str, str]]:
    """
    Compara snapshots mensuales de los 3 principales competidores y genera alertas si hay cambios significativos.
    snapshots: lista de dicts, cada uno con: {
        'name': str,
        'history': [
            {'date': '2025-11', 'rating': float, 'reviews': int, 'photos': int},
            ...
        ]
    }
    country: código país para internacionalización de triggers.
    """
    alerts = []
    now = datetime.datetime.now()
    month = now.month
    # Festividades por país
    holidays = {
        'US': {12: 'Navidad'},
        'MX': {12: 'Navidad'},
        'BR': {12: 'Natal'},
        'AR': {12: 'Navidad'},
    }
    for comp in snapshots:
        name = comp['name']
        hist = comp['history']
        if len(hist) < 2:
            continue
        prev, curr = hist[-2], hist[-1]
        # Trigger: rating sube +0.2
        if curr['rating'] - prev['rating'] > 0.2:
            alerts.append({
                'type': 'rating',
                'alert': f"Tu rival {name} ha subido su rating a {curr['rating']:.1f}. ¡Reacciona antes de perder ranking!"
            })
        # Trigger: >5 fotos nuevas en un mes
        if curr['photos'] - prev['photos'] > 5:
            alerts.append({
                'type': 'photos',
                'alert': f"Tu rival {name} ha publicado muchas fotos nuevas este mes. ¡Actualiza tu perfil visual!"
            })
        # Trigger: reviews suben mucho
        if curr['reviews'] - prev['reviews'] > 20:
            alerts.append({
                'type': 'reviews',
                'alert': f"{name} está recibiendo muchas reseñas nuevas. Responde y mejora tu reputación."
            })
        # Trigger: fotos navideñas en diciembre
        if month == 12 and country in holidays:
            fest = holidays[country][12]
            if curr['photos'] > prev['photos'] and 'navidad' in curr.get('tags', '').lower():
                alerts.append({
                    'type': 'holiday',
                    'alert': f"{name} ha subido fotos de {fest}. ¡No te quedes atrás en la temporada!"
                })
    return alerts


# --- Integración avanzada con Gemini para auditoría de marketing local ---
import os
import google.generativeai as genai

def redactar_alerta_gemini(alert: Dict[str, str], lang: str = 'es', contexto: Dict = None) -> Dict:
    """
    Llama a Gemini API con prompt avanzado para obtener recomendaciones tipo consultoría.
    Estructura de respuesta: JSON con QuickWin, StrategicGap, TechnicalFix.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "QuickWin": "[Error: Falta GEMINI_API_KEY]",
            "StrategicGap": "[Error: Falta GEMINI_API_KEY]",
            "TechnicalFix": "[Error: Falta GEMINI_API_KEY]"
        }
    genai.configure(api_key=api_key)

    # Contexto de negocio enriquecido
    contexto = contexto or {}
    rubro = contexto.get("rubro", "Negocio local")
    competencia = contexto.get("competencia", "No detectada")
    fallo = contexto.get("fallo", "No especificado")
    pais = contexto.get("pais", "ES")

    # System prompt avanzado
    system_prompt = (
        "Eres un experto en Growth Hacking para negocios locales. "
        "Tu tono es directo, profesional y enfocado en el retorno de inversión (ROI). "
        "No des consejos obvios. Audita bajo estándares de conversión de marketing local. "
        f"Rubro: {rubro}. "
        f"Competencia detectada: {competencia}. "
        f"Fallo crítico: {fallo}. "
        f"País: {pais}. "
        "Responde en JSON con las claves: QuickWin, StrategicGap, TechnicalFix. "
        "Si el país es Brasil, responde en portugués nativo con jerga empresarial local."
    )

    # Mensaje de usuario (input)
    user_prompt = alert.get('alert', 'Audita el negocio y genera recomendaciones.')

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([
        {"role": "system", "parts": [system_prompt]},
        {"role": "user", "parts": [user_prompt]}
    ])

    # Intentar extraer JSON del output
    import json
    try:
        # Gemini puede devolver texto, intentamos extraer el JSON
        text = response.text.strip()
        # Buscar primer y último corchete para extraer JSON
        start = text.find('{')
        end = text.rfind('}')+1
        if start != -1 and end != -1:
            json_str = text[start:end]
            return json.loads(json_str)
        else:
            return {"QuickWin": "[Formato inesperado]", "StrategicGap": text, "TechnicalFix": "[Revisar output]"}
    except Exception as e:
        return {"QuickWin": "[Error de parsing]", "StrategicGap": str(e), "TechnicalFix": "[Revisar output]"}
