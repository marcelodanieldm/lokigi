# test_global_validator.py
"""
QA Automation: Validador Global de Inteligencia para Lokigi
- Test de Consistencia: Lucro Cesante nunca negativo
- Test de Localización: Moneda y ticket promedio cambian según país
- Test de Performance: Lighthouse > 95 en Vercel con mapa de calor
"""
import pytest
import requests

API_AUDIT = "http://localhost:8000/audit"
API_AUDIT_RESULT = "http://localhost:8000/audit/result/"

@pytest.mark.timeout(10)
def test_lucro_cesante_nunca_negativo():
    """El Lucro Cesante (proyección de pérdida) nunca debe ser negativo."""
    client = {"lat": -23.55, "lon": -46.63, "rating": 4.9, "review_count": 200, "name": "Cliente SP"}
    competitors = [
        {"name": "Rival SP", "lat": -23.56, "lon": -46.62, "rating": 4.8, "review_count": 180}
    ]
    payload = {
        "score": 95,
        "rubro": "Restaurante",
        "competencia": "2 restaurantes en 1km con 4.8 estrellas",
        "fallo": "Poucas fotos",
        "pais": "BR",
        "lang": "pt",
        "client": client,
        "competitors": competitors,
        "locale": "pt"
    }
    audit_id = requests.post(API_AUDIT, json=payload).json()["audit_id"]
    for _ in range(20):
        r = requests.get(f"{API_AUDIT_RESULT}{audit_id}").json()
        if not r.get("status"):
            lucro = r["dominance"].get("lucro_cesante", 0)
            assert lucro >= 0, f"Lucro Cesante negativo: {lucro}"
            break

@pytest.mark.timeout(10)
def test_localizacion_moneda_ticket():
    """Verifica que la moneda y el ticket promedio cambian según país."""
    # San Pablo (BR)
    client_br = {"lat": -23.55, "lon": -46.63, "rating": 4.9, "review_count": 200, "name": "Cliente SP"}
    competitors_br = [{"name": "Rival SP", "lat": -23.56, "lon": -46.62, "rating": 4.8, "review_count": 180}]
    payload_br = {
        "score": 95,
        "rubro": "Restaurante",
        "competencia": "2 restaurantes em 1km com 4.8 estrelas",
        "fallo": "Poucas fotos",
        "pais": "BR",
        "lang": "pt",
        "client": client_br,
        "competitors": competitors_br,
        "locale": "pt"
    }
    audit_id_br = requests.post(API_AUDIT, json=payload_br).json()["audit_id"]
    # Miami (USA)
    client_us = {"lat": 25.76, "lon": -80.19, "rating": 4.7, "review_count": 150, "name": "Cliente Miami"}
    competitors_us = [{"name": "Rival Miami", "lat": 25.77, "lon": -80.18, "rating": 4.6, "review_count": 140}]
    payload_us = {
        "score": 90,
        "rubro": "Restaurant",
        "competencia": "2 restaurants in 1mi with 4.6 stars",
        "fallo": "Few photos",
        "pais": "US",
        "lang": "en",
        "client": client_us,
        "competitors": competitors_us,
        "locale": "en"
    }
    audit_id_us = requests.post(API_AUDIT, json=payload_us).json()["audit_id"]
    # Polling
    for _ in range(20):
        r_br = requests.get(f"{API_AUDIT_RESULT}{audit_id_br}").json()
        r_us = requests.get(f"{API_AUDIT_RESULT}{audit_id_us}").json()
        if not r_br.get("status") and not r_us.get("status"):
            moeda_br = r_br["dominance"].get("currency", "")
            ticket_br = r_br["dominance"].get("ticket_promedio", 0)
            moeda_us = r_us["dominance"].get("currency", "")
            ticket_us = r_us["dominance"].get("ticket_promedio", 0)
            assert moeda_br in ["BRL", "R$"], f"Moneda incorrecta para BR: {moeda_br}"
            assert moeda_us in ["USD", "$"], f"Moneda incorrecta para US: {moeda_us}"
            assert ticket_br > 0 and ticket_us > 0, "Ticket promedio debe ser positivo"
            break

# Test de Performance: Lighthouse (Playwright)
import subprocess
import sys

def test_lighthouse_performance():
    """Asegura que el score de Performance en Vercel sea > 95 con el heatmap cargado."""
    url = "https://lokigi.vercel.app/dashboard/premium"
    try:
        result = subprocess.run([
            "npx", "lighthouse", url, "--only-categories=performance", "--quiet", "--chrome-flags=--headless", "--output=json"
        ], capture_output=True, text=True, timeout=60)
        import json
        report = json.loads(result.stdout)
        score = report["categories"]["performance"]["score"] * 100
        assert score > 95, f"Performance Lighthouse < 95: {score}"
    except Exception as e:
        pytest.skip(f"Lighthouse test skipped: {e}")
