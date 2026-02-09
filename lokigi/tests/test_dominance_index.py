# test_dominance_index.py
"""
Pruebas automáticas para Dominance Index API de Lokigi
- Valida cálculo, amenaza y unidad internacionalizada
"""
import requests

API_URL = "http://localhost:8000/dominance-index"

def test_dominance_index_pt():
    payload = {
        "client": {"lat": 38.7223, "lon": -9.1393, "rating": 4.8, "review_count": 120, "name": "Mi Negocio"},
        "competitors": [
            {"name": "Barberia Lisboa", "lat": 38.723, "lon": -9.14, "rating": 4.7, "review_count": 200},
            {"name": "Corte Moderno", "lat": 38.721, "lon": -9.138, "rating": 4.9, "review_count": 80},
            {"name": "Estilo Urbano", "lat": 38.725, "lon": -9.142, "rating": 4.5, "review_count": 150},
            {"name": "Look Total", "lat": 38.720, "lon": -9.137, "rating": 4.6, "review_count": 60},
            {"name": "Cabelo & Arte", "lat": 38.724, "lon": -9.141, "rating": 4.8, "review_count": 110}
        ],
        "locale": "pt"
    }
    resp = requests.post(API_URL, json=payload, timeout=8)
    assert resp.status_code == 200, f"Status inesperado: {resp.status_code}"
    data = resp.json()
    assert "dominance_index" in data and 0 < data["dominance_index"] < 1, "Dominance Index fuera de rango"
    assert data["unit"] == "km", "Unidad incorrecta para PT"
    assert data["competitor_threat"] == "Barberia Lisboa", "Amenaza incorrecta"
    print("✔ Dominance Index PT OK")

def test_dominance_index_en():
    payload = {
        "client": {"lat": 40.7128, "lon": -74.0060, "rating": 4.5, "review_count": 100, "name": "NYC Client"},
        "competitors": [
            {"name": "Alpha Barbers", "lat": 40.713, "lon": -74.01, "rating": 4.7, "review_count": 200},
            {"name": "Beta Cuts", "lat": 40.711, "lon": -74.005, "rating": 4.6, "review_count": 150},
            {"name": "Gamma Style", "lat": 40.715, "lon": -74.008, "rating": 4.8, "review_count": 180},
            {"name": "Delta Look", "lat": 40.710, "lon": -74.003, "rating": 4.4, "review_count": 90},
            {"name": "Epsilon Hair", "lat": 40.714, "lon": -74.007, "rating": 4.5, "review_count": 120}
        ],
        "locale": "en"
    }
    resp = requests.post(API_URL, json=payload, timeout=8)
    assert resp.status_code == 200, f"Status inesperado: {resp.status_code}"
    data = resp.json()
    assert data["unit"] == "mi", "Unidad incorrecta para EN"
    print("✔ Dominance Index EN OK")

if __name__ == "__main__":
    print("Ejecutando pruebas Dominance Index...")
    test_dominance_index_pt()
    test_dominance_index_en()
    print("Todas las pruebas pasaron.")
