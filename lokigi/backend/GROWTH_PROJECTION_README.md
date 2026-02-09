# GROWTH_PROJECTION_README.md

# Algoritmo de Crecimiento Proyectado

**Ubicación:** backend/growth_projection.py

## Objetivo
Comparar métricas antes/después y proyectar la ganancia del cliente para los próximos 6 meses gracias a Lokigi.

## Funcionalidades
- **Comparación de Scores:** Calcula el incremento porcentual de visibilidad basado en la mejora del score.
- **Proyección de ROI:** Estima la ganancia extra para los próximos 180 días según el daily_revenue y la mejora de visibilidad.
- **Visual Data:** Genera un dataset para gráfico radar (Reputación, SEO Local, Contenido Visual, NAP Consistency antes/después).
- **Internacionalización:** Ajusta la moneda y símbolo según la región (ARS, BRL, USD).


## Ejemplo de Uso (Python)
```python
from growth_projection import project_growth

initial = {"reputation": 60, "seo": 55, "visual": 50, "nap": 70}
final = {"reputation": 80, "seo": 75, "visual": 85, "nap": 90}
result = project_growth(
    initial_score=58,
    final_score=82,
    initial_metrics=initial,
    final_metrics=final,
    daily_revenue=120,
    currency="ARS"
)
print(result)
```

## API REST
- **POST /growth/projection**
  - Body:
    ```json
    {
      "initial_score": 58,
      "final_score": 82,
      "initial_metrics": {"reputation": 60, "seo": 55, "visual": 50, "nap": 70},
      "final_metrics": {"reputation": 80, "seo": 75, "visual": 85, "nap": 90},
      "daily_revenue": 120,
      "currency": "ARS"
    }
    ```
  - Response: igual al output esperado abajo.


## Visualización Frontend
- El dashboard premium consume este endpoint y muestra la proyección y un gráfico radar (SVG/Canvas, sin librerías pesadas).
- Ver integración en `frontend/src/app/dashboard/premium/page.tsx`.

## Tests Automáticos
- Archivo: `tests/test_growth_projection.py`
- Valida:
  - Cálculo de visibilidad y ganancia
  - Dataset para radar chart
  - Internacionalización de moneda

Ejecuta:
```bash
pytest tests/test_growth_projection.py
```

## Output esperado
```json
{
  "visibility_gain_pct": 28.8,
  "projected_gain": 6220.8,
  "currency": "ARS",
  "currency_symbol": "$",
  "radar": {
    "labels": ["Reputación", "SEO Local", "Contenido Visual", "Consistencia NAP"],
    "datasets": [
      {"label": "Antes", "data": [60, 55, 50, 70]},
      {"label": "Después", "data": [80, 75, 85, 90]}
    ]
  }
}
```

---

**Autor:** Chief Data Scientist, Lokigi
**Fecha:** 2025-12-29
