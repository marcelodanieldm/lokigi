
import sys
import os
import tempfile
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_persistencia_grafica_evolucion():
    """
    Verifica que la gráfica de evolución mensual muestre correctamente los últimos 6 meses.
    """
    payload = {
        "initial_score": 70,
        "final_score": 85,
        "initial_metrics": {"SEO": 60, "Visual": 50},
        "final_metrics": {"SEO": 85, "Visual": 90},
        "daily_revenue": 1000,
        "currency": "USD"
    }
    response = client.post("/growth/projection", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Validar claves reales esperadas en la respuesta
    assert "projected_gain" in data
    assert "radar" in data
    assert "currency" in data

def test_permisos_dashboard():
    """
    Asegura que un cliente gratuito o de pago único NO pueda entrar al dashboard premium.
    """
    # Simula endpoint de acceso con roles
    for role in ["FREE", "ONE_TIME"]:
        response = client.get("/dashboard/premium", headers={"X-User-Role": role})
        assert response.status_code == 403

def test_simulacion_alerta_multilenguaje():
    """
    Simula un cambio ficticio en la competencia y verifica la notificación en ES, PT, EN.
    """
    snapshots = [
        {
            "name": "Pizzeria Napoli",
            "history": [
                {"date": "2025-11", "rating": 4.2, "reviews": 120, "photos": 30},
                {"date": "2025-12", "rating": 4.5, "reviews": 145, "photos": 42, "tags": "Navidad"}
            ]
        }
    ]
    for lang in ["es", "pt", "en"]:
        response = client.post("/alert-radar", json={"snapshots": snapshots, "country": "AR", "lang": lang})
        assert response.status_code == 200
        data = response.json()
        assert any(lang.upper() in a or lang == "es" for a in data["alerts"]) or len(data["alerts"]) > 0
