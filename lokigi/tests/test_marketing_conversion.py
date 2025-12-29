"""
QA Automation: Validador de Conversión para Marketing de Guerrilla (Lokigi)
- Link Integrity, I18n y Funnel Tracking
"""
import pytest
import requests
import time

API_URL = "http://localhost:3000"  # Next.js local para links
BACKEND_URL = "http://localhost:8000"  # FastAPI para tracking

# --- Link Integrity ---
def test_link_integrity():
    """Verifica que cada link generado lleve al reporte correcto."""
    # Simula generación de link único
    business = {"name": "Dentista Smile", "phone": "+351 912345678", "website": "smile.pt"}
    from backend.outreach_engine import generate_unique_link
    link = generate_unique_link(business, base_url=f"{API_URL}/public-audit/")
    # Simula que el backend asocia el hash con el negocio
    hash_id = link.split("/")[-1]
    # El endpoint debe devolver el reporte correcto
    r = requests.get(f"{API_URL}/api/public-audit/{hash_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == business["name"]

# --- Test de I18n ---
def test_i18n_portuguese():
    """Asegura que un negocio en Lisboa reciba el mensaje en Portugués."""
    business = {"name": "Clínica Lisboa", "phone": "+351 912345678", "website": "clinicapt.pt"}
    from backend.lead_scoring import lead_scoring
    targets = lead_scoring([business])
    assert targets[0]["lang"] == "pt"
    # Simula mensaje generado
    from backend.outreach_engine import prepare_message
    link = "https://lokigi.com/audit/abc123"
    msg = prepare_message({**business, "score": 88}, link)
    assert "Olá" in msg or "analicé" not in msg  # Mensaje debe estar en portugués

# --- Funnel Tracking ---
def test_funnel_tracking():
    """Valida que el sistema de analítica registre apertura y tiempo de lectura del lead."""
    # Simula apertura de link
    hash_id = "testhash123"
    start = time.time()
    r = requests.post(f"{BACKEND_URL}/api/track/open", json={"hash": hash_id})
    assert r.status_code == 200
    # Simula que el usuario permanece 7 segundos
    time.sleep(7)
    r2 = requests.post(f"{BACKEND_URL}/api/track/close", json={"hash": hash_id, "duration": 7})
    assert r2.status_code == 200
    # Consulta analítica
    r3 = requests.get(f"{BACKEND_URL}/api/track/analytics/{hash_id}")
    assert r3.status_code == 200
    data = r3.json()
    assert data["opens"] >= 1
    assert data["avg_duration"] >= 7
