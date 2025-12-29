# Algoritmo de Radar de Alertas (Detección de Anomalías Competitivas)

## Objetivo
Detectar cambios significativos en los competidores y generar alertas de "peligro" para el usuario de Lokigi.

## Implementación

### 1. Data Tracking
- La función `detect_competitor_anomalies` compara los snapshots mensuales de los 3 principales competidores.
- Analiza cambios en: Ranking (rating), Reviews, Fotos.

### 2. Triggers de Alerta
- **Rating:** Si un competidor sube +0.2 puntos en el mes.
- **Fotos:** Si publica más de 5 fotos nuevas en el mes.
- **Reviews:** Si recibe más de 10 reseñas nuevas en el mes.
- **Festividades:** En diciembre (Latam/USA/BR), alerta si suben fotos navideñas (tags).

### 3. Generación de Insight
- Cada alerta se envía a Gemini (Google Generative AI) para redactar un insight breve y urgente, adaptado al idioma y contexto.
- Ejemplo: 'Tu rival [X] ha actualizado sus fotos; podrías bajar en el ranking si no reaccionas'.

### 4. Internacionalización
- Los triggers de festividad se adaptan a las costumbres locales según el país (ej. Navidad/Natal).
- El insight se genera en el idioma del usuario (ES, PT, EN).

## Uso

```python
from alert_radar import detect_competitor_anomalies, generate_alert_insights

snapshots = [
    {
        'name': 'Competidor A',
        'history': [
            {'date': '2025-11-01', 'rating': 4.5, 'reviews': 120, 'photos': 30, 'photo_tags': ''},
            {'date': '2025-12-01', 'rating': 4.7, 'reviews': 135, 'photos': 38, 'photo_tags': 'Navidad'}
        ]
    },
    ...
]
alerts = detect_competitor_anomalies(snapshots, country='MX')
insights = generate_alert_insights(alerts, lang='es')
```

## Documentación de funciones
- `detect_competitor_anomalies(snapshots, country)`: Devuelve lista de dicts con alertas detectadas.
- `generate_alert_insights(alerts, lang, contexto)`: Devuelve lista de textos breves generados por Gemini.

---

**Lead Data Scientist: Algoritmo validado y listo para producción.**
