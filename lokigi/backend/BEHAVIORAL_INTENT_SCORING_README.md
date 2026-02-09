# Behavioral Intent Scoring - Documentación

## Objetivo
Identificar la intención de compra de un lead en Lokigi, analizando su comportamiento en el reporte gratuito. El modelo asigna un score de 0 a 100 y automatiza acciones de marketing según el resultado.

## Entradas del Modelo
- **tiempo_permanencia (float):** Minutos totales en el reporte.
- **num_clicks_competencia (int):** Clics en la comparativa de competencia.
- **descargo_pdf (bool):** Si descargó el PDF gratuito.
- **vistas_reporte (int):** Veces que abrió el reporte en la última hora.
- **ultima_compra (datetime | None):** Fecha/hora de última compra.
- **ultima_interaccion (datetime):** Última interacción con el reporte.
- **seccion_mas_vista (str):** Sección donde pasó más tiempo ("heatmap", "comparativa", etc).

## Lógica de Scoring
- **Score base:**
  - Tiempo en reporte: hasta 45 pts
  - Clics en competencia: hasta 30 pts
  - Descarga PDF: 10 pts
  - Vistas del reporte: hasta 15 pts
- **Score máximo:** 100

## Disparadores y Acciones
- **Alerta de Intención Alta:**
  - Score > 80 y al menos 2 vistas en 1 hora.
  - Motivo personalizado según sección más vista.
- **Cupón de Descuento Dinámico:**
  - Si score > 80 y no compró en 24h, se genera cupón Stripe del 15% válido por 4 horas.

## Personalización de Seguimiento
El motivo del seguimiento se adapta a la sección más vista:
- **heatmap:** "Interés alto en visibilidad geográfica de tu negocio."
- **comparativa:** "Interés en comparativa con la competencia."
- **alertas:** "Atención a alertas de oportunidad."
- **pdf:** "Descargó el reporte para análisis detallado."

## Ejemplo de Uso
```python
from backend.behavioral_intent_scoring import behavioral_intent_score
from datetime import datetime

resultado = behavioral_intent_score(
    tiempo_permanencia=18.5,
    num_clicks_competencia=7,
    descargo_pdf=True,
    vistas_reporte=3,
    ultima_compra=None,
    ultima_interaccion=datetime.utcnow(),
    seccion_mas_vista="heatmap"
)
print(resultado)
```

## Integración
- Llamar este modelo tras cada interacción relevante en el frontend/backend.
- Si `resultado['alerta']` es True, disparar alerta y seguimiento personalizado.
- Si `resultado['generar_cupon']` es True, crear cupón Stripe y notificar al usuario.

---
Última actualización: 2025-12-29
