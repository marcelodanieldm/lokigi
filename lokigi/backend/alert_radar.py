# backend/alert_radar.py
"""
Motor de Detección de Anomalías Competitivas para Lokigi
"""
import datetime
from typing import List, Dict, Any

def detect_competitor_anomalies(snapshots: List[Dict[str, Any]], country: str = "US") -> List[Dict[str, str]]:
    """
    Motor de Detección de Anomalías Competitivas (Radar de Alertas)
    - Compara snapshots mensuales de los 3 principales competidores y genera alertas si hay cambios significativos.
    - Umbrales: rating +0.2, >5 fotos/mes, >10 reviews/mes.
    - Internacionalización: adapta triggers a festividades locales (ej. fotos navideñas en diciembre).
    snapshots: lista de dicts, cada uno con:
      {
        'name': str,
        'history': [
            {'date': '2025-11-01', 'rating': float, 'reviews': int, 'photos': int, 'photo_tags': str},
            ... (ordenados por fecha ascendente)
        ]
      }
    country: código país (para adaptar triggers a festividades)
    Return: lista de alertas detectadas (dicts)
    """
    alerts = []
    now = datetime.datetime.utcnow()
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
        # Trigger 1: Rating sube +0.2
        if curr['rating'] - prev['rating'] > 0.2:
            alerts.append({
                'type': 'rating',
                'competitor': name,
                'delta': round(curr['rating'] - prev['rating'], 2),
                'alert': f"Tu rival {name} ha subido su rating a {curr['rating']} (+{curr['rating']-prev['rating']:.2f}). ¡Reacciona antes de perder ranking!"
            })
        # Trigger 2: >5 fotos nuevas en un mes
        if curr['photos'] - prev['photos'] > 5:
            alerts.append({
                'type': 'photos',
                'competitor': name,
                'delta': curr['photos'] - prev['photos'],
                'alert': f"Tu rival {name} ha publicado {curr['photos']-prev['photos']} fotos nuevas este mes. ¡Actualiza tu perfil visual!"
            })
        # Trigger 3: reviews suben mucho
        if curr['reviews'] - prev['reviews'] > 10:
            alerts.append({
                'type': 'reviews',
                'competitor': name,
                'delta': curr['reviews'] - prev['reviews'],
                'alert': f"{name} está recibiendo {curr['reviews']-prev['reviews']} reseñas nuevas. Responde y mejora tu reputación."
            })
        # Trigger 4: Festividades (ej. fotos navideñas en diciembre)
        if month == 12 and country in holidays:
            fest = holidays[country][12]
            if curr['photos'] > prev['photos'] and fest.lower() in (curr.get('photo_tags','')+prev.get('photo_tags','')).lower():
                alerts.append({
                    'type': 'holiday',
                    'competitor': name,
                    'alert': f"{name} ha publicado fotos de {fest}. ¡No te quedes atrás en la temporada!"
                })
    return alerts

# Generación de insight con Gemini
def generate_alert_insights(alerts: List[Dict[str, str]], lang: str = 'es', contexto: Dict = None) -> List[str]:
    """
    Envía cada alerta a Gemini para redactar un insight breve y urgente.
    """
    insights = []
    for alert in alerts:
        insight = redactar_alerta_gemini(alert, lang=lang, contexto=contexto)
        if isinstance(insight, dict) and 'QuickWin' in insight:
            insights.append(insight['QuickWin'])
        elif isinstance(insight, dict) and 'text' in insight:
            insights.append(insight['text'])
        else:
            insights.append(str(insight))
    return insights


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
