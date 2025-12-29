"""
Dominance Index y Mapa de Calor de Rivalidad para Lokigi

Lead Data Scientist: Algoritmo de Proximidad y Dominancia

- Calcula el Dominance Index de un negocio usando la Ley de Gravitación de Reilly adaptada.
- Entrada: coordenadas GPS del cliente y lista de 5 competidores cercanos (con rating y review_count).
- Output: Dominance Index, Competidor Amenaza, y datos para mapa de calor.
- Internacionalización: soporta km (ES/PT) y millas (EN).
"""
import math
from typing import List, Dict, Literal

# Utilidad para calcular distancia Haversine

def haversine(lat1, lon1, lat2, lon2, unit: Literal["km", "mi"] = "km"):
    R = 6371 if unit == "km" else 3958.8  # Radio de la Tierra en km o millas
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def dominance_index(
    client: Dict,  # {"lat": float, "lon": float, "rating": float, "review_count": int}
    competitors: List[Dict],  # [{"lat", "lon", "rating", "review_count", "name"}]
    locale: str = "es"
) -> Dict:
    """
    Calcula el Dominance Index y el Competidor Amenaza.
    locale: 'es', 'pt' = km; 'en' = millas
    """
    unit = "km" if locale in ["es", "pt"] else "mi"
    client_power = client["rating"] * client["review_count"]
    results = []
    for comp in competitors:
        dist = haversine(client["lat"], client["lon"], comp["lat"], comp["lon"], unit)
        comp_power = comp["rating"] * comp["review_count"]
        # Ley de Reilly: Atracción = poder / distancia^2
        attraction = comp_power / (dist**2 + 1e-6)  # Evita división por cero
        results.append({
            "name": comp["name"],
            "distance": dist,
            "power": comp_power,
            "attraction": attraction
        })
    # Dominance Index: proporción de poder del cliente vs suma total
    total_attraction = client_power + sum(r["attraction"] for r in results)
    dominance = client_power / total_attraction if total_attraction > 0 else 0
    # Competidor Amenaza: mayor attraction
    threat = max(results, key=lambda r: r["attraction"])
    # Mapa de calor: lista de atracciones
    heatmap = [{"name": "Cliente", "lat": client["lat"], "lon": client["lon"], "attraction": client_power}]
    for r, comp in zip(results, competitors):
        heatmap.append({"name": comp["name"], "lat": comp["lat"], "lon": comp["lon"], "attraction": r["attraction"]})
    return {
        "dominance_index": round(dominance, 3),
        "competitor_threat": threat["name"],
        "heatmap": heatmap,
        "unit": unit
    }

# Ejemplo de uso
def _demo():
    client = {"lat": 38.7223, "lon": -9.1393, "rating": 4.8, "review_count": 120}
    competitors = [
        {"name": "Barberia Lisboa", "lat": 38.723, "lon": -9.14, "rating": 4.7, "review_count": 200},
        {"name": "Corte Moderno", "lat": 38.721, "lon": -9.138, "rating": 4.9, "review_count": 80},
        {"name": "Estilo Urbano", "lat": 38.725, "lon": -9.142, "rating": 4.5, "review_count": 150},
        {"name": "Look Total", "lat": 38.720, "lon": -9.137, "rating": 4.6, "review_count": 60},
        {"name": "Cabelo & Arte", "lat": 38.724, "lon": -9.141, "rating": 4.8, "review_count": 110},
    ]
    print(dominance_index(client, competitors, locale="pt"))

if __name__ == "__main__":
    _demo()
