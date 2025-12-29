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

# Ejemplo de integración con Gemini (simulado)
def redactar_alerta_gemini(alert: Dict[str, str], lang: str = 'es') -> str:
    # Aquí se llamaría a la IA real, simulado para demo
    base = alert['alert']
    if lang == 'pt':
        return f"[PT] {base}"
    elif lang == 'en':
        return f"[EN] {base}"
    return base
