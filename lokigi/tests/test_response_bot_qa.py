# test_response_bot_qa.py
"""
QA Automation para el Bot de Respuestas (Pytest)
- Test de Alucinaciones: la IA no inventa servicios (cruza con DB)
- Test de Idioma: respuesta en Portugués nativo, sin 'Portuñol'
- Test de Estrés de UI: aprobación masiva de 50 reseñas
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Simulación de DB de negocio
BUSINESS_DB = {
    "pizzeria_roma": {
        "services": ["pizza", "pasta", "ensaladas"],
        "lang": "pt",
        "desc": "Pizzaria tradicional com forno a lenha."
    }
}

# --- Test de Alucinaciones ---
def test_no_hallucinations():
    """La IA no debe inventar servicios que no están en la DB del negocio."""
    review = "Amei o sushi e o atendimento!"
    business = BUSINESS_DB["pizzeria_roma"]
    resp = client.post(
        "/worker/generate-replies",
        json={
            "reviews": [review],
            "temperature": 0.7,
            "tone": "Professional",
            "lang": business["lang"]
        },
        headers={"X-User-Role": "WORKER"}
    )
    assert resp.status_code == 200
    suggestion = resp.json()["suggestions"][0].lower()
    # No debe mencionar sushi
    assert "sushi" not in suggestion
    # Debe mencionar solo servicios reales si los menciona
    for word in ["pizza", "pasta", "ensalada", "forno", "lenha"]:
        if word in suggestion:
            assert word in business["desc"] or word in business["services"]

# --- Test de Idioma ---
def test_no_portunol():
    """La respuesta debe ser Portugués nativo, no Portuñol."""
    review = "Excelente atendimento e ambiente!"
    resp = client.post(
        "/worker/generate-replies",
        json={
            "reviews": [review],
            "temperature": 0.7,
            "tone": "Professional",
            "lang": "pt"
        },
        headers={"X-User-Role": "WORKER"}
    )
    assert resp.status_code == 200
    suggestion = resp.json()["suggestions"][0]
    # No debe contener palabras en español típicas
    for word in ["gracias", "servicio", "ambiente", "excelente"]:
        assert word not in suggestion.lower()
    # Debe contener palabras en portugués
    assert any(pt in suggestion.lower() for pt in ["obrigado", "atendimento", "ambiente", "excelente"])

# --- Test de Estrés de UI ---
import time

def test_ui_stress():
    """Aprobar 50 reseñas en menos de 10 segundos (simulación de cola)."""
    reviews = [f"Reseña {i}" for i in range(50)]
    start = time.time()
    resp = client.post(
        "/worker/generate-replies",
        json={
            "reviews": reviews,
            "temperature": 0.7,
            "tone": "Professional",
            "lang": "es"
        },
        headers={"X-User-Role": "WORKER"}
    )
    elapsed = time.time() - start
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["suggestions"]) == 50
    assert elapsed < 10, f"Demoró demasiado: {elapsed:.2f}s"
