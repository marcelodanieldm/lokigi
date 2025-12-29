# Dominance Index y Mapa de Calor de Rivalidad

## Objetivo
Determinar el grado de dominancia de un negocio en su zona y detectar el "Competidor Amenaza" usando una variante de la Ley de Gravitación de Reilly.

## Lógica
- **Dominance Index:** Proporción del poder de atracción del cliente respecto al total (cliente + competidores).
- **Competidor Amenaza:** El competidor con mayor "attraction" (rating * reviews / distancia²).
- **Mapa de Calor:** Lista de puntos con nivel de atracción para visualización.
- **Internacionalización:**
  - 'es', 'pt' → km
  - 'en' → millas

## Ejemplo de Uso

```python
from dominance_index import dominance_index

client = {"lat": 38.7223, "lon": -9.1393, "rating": 4.8, "review_count": 120}
competitors = [
    {"name": "Barberia Lisboa", "lat": 38.723, "lon": -9.14, "rating": 4.7, "review_count": 200},
    {"name": "Corte Moderno", "lat": 38.721, "lon": -9.138, "rating": 4.9, "review_count": 80},
    {"name": "Estilo Urbano", "lat": 38.725, "lon": -9.142, "rating": 4.5, "review_count": 150},
    {"name": "Look Total", "lat": 38.720, "lon": -9.137, "rating": 4.6, "review_count": 60},
    {"name": "Cabelo & Arte", "lat": 38.724, "lon": -9.141, "rating": 4.8, "review_count": 110},
]
result = dominance_index(client, competitors, locale="pt")
print(result)
```

## Output esperado
```json
{
  "dominance_index": 0.41,
  "competitor_threat": "Barberia Lisboa",
  "heatmap": [
    {"name": "Cliente", "lat": 38.7223, "lon": -9.1393, "attraction": 576.0},
    {"name": "Barberia Lisboa", "lat": 38.723, "lon": -9.14, "attraction": 1999999.999},
    ...
  ],
  "unit": "km"
}
```

## Notas
- El cálculo de distancia usa la fórmula de Haversine.
- El heatmap puede usarse para visualización en frontend (Leaflet, Mapbox, etc).
- El algoritmo es internacionalizable y robusto para retail/locales.

---

Para detalles, ver `backend/dominance_index.py`.
