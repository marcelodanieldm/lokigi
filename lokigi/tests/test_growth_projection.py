# test_growth_projection.py
"""
Tests automáticos para el endpoint de Crecimiento Proyectado
- Valida cálculo de visibilidad, ganancia y radar chart
- Valida internacionalización de moneda
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_growth_projection_basic():
    resp = client.post(
        "/growth/projection",
        json={
            "initial_score": 60,
            "final_score": 80,
            "initial_metrics": {"reputation": 60, "seo": 55, "visual": 50, "nap": 70},
            "final_metrics": {"reputation": 80, "seo": 75, "visual": 85, "nap": 90},
            "daily_revenue": 100,
            "currency": "USD"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert 0 < data["visibility_gain_pct"] <= 100
    assert data["projected_gain"] > 0
    assert data["currency"] == "USD"
    assert "radar" in data and "labels" in data["radar"]


def test_growth_projection_currency():
    for region, symbol in [("ARS", "$"), ("BRL", "R$"), ("USD", "$")]:
        resp = client.post(
            "/growth/projection",
            json={
                "initial_score": 50,
                "final_score": 70,
                "initial_metrics": {"reputation": 50, "seo": 50, "visual": 50, "nap": 50},
                "final_metrics": {"reputation": 70, "seo": 70, "visual": 70, "nap": 70},
                "daily_revenue": 200,
                "currency": region
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["currency_symbol"] == symbol
        assert data["currency"] == region
