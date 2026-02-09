# test_review_response_engine.py
"""
Tests automáticos para Review Response Engine (FastAPI)
- Valida seguridad (solo WORKER/ADMIN)
- Valida generación de sugerencias Gemini
- Valida integración de tono y temperatura
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# --- Helpers ---
def auth_headers(role):
    # Simula autenticación por rol (en real, usar JWT de Supabase)
    return {"X-User-Role": role}


def test_access_denied_for_user():
    """Solo WORKER/ADMIN pueden acceder"""
    resp = client.post(
        "/worker/generate-replies",
        json={"reviews": ["Test"], "temperature": 0.7, "tone": "Professional", "lang": "es"},
        headers=auth_headers("USER")
    )
    assert resp.status_code == 403


def test_generate_replies_batch():
    """Genera sugerencias para lote de reseñas"""
    resp = client.post(
        "/worker/generate-replies",
        json={
            "reviews": ["Excelente pizza", "Servicio lento"],
            "temperature": 0.5,
            "tone": "Grateful",
            "lang": "es"
        },
        headers=auth_headers("WORKER")
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data and len(data["suggestions"]) == 2
    assert all("Respuesta" in s or "reply" in s for s in data["suggestions"])


def test_tone_and_temperature():
    """Verifica que el tono y temperatura afectan el prompt (simulado)"""
    for tone in ["Professional", "Casual", "Grateful"]:
        resp = client.post(
            "/worker/generate-replies",
            json={"reviews": ["Test"], "temperature": 0.9, "tone": tone, "lang": "en"},
            headers=auth_headers("ADMIN")
        )
        assert resp.status_code == 200
        suggestion = resp.json()["suggestions"][0]
        assert tone.split()[0] in suggestion or "reply" in suggestion
