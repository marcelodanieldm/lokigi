"""
Suite de pruebas automatizadas para el Dashboard Premium (Control Tower)
- Persistencia, permisos y alertas multilingües
"""
import pytest
import requests

API_URL = "http://localhost:3000"  # Next.js local

# --- Test de Persistencia ---
def test_evolucion_mensual_persistencia():
    """Verifica que la gráfica de evolución mensual muestre los últimos 6 meses sin errores de renderizado ni datos nulos."""
    user_id = "premium-user-demo"
    r = requests.get(f"{API_URL}/api/dashboard/evolution?user_id={user_id}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["months"]) == 6
    assert all(isinstance(m, str) for m in data["months"])
    assert all(isinstance(v, (int, float)) for v in data["values"])
    # Simula renderizado (ejemplo: no debe haber None)
    assert all(v is not None for v in data["values"])

# --- Test de Permisos ---
@pytest.mark.parametrize("user_id,expected_status", [
    ("free-user-demo", 302),
    ("oneoff-user-demo", 302),
    ("premium-user-demo", 200),
])
def test_dashboard_permisos(user_id, expected_status):
    """Asegura que solo usuarios premium acceden al dashboard."""
    r = requests.get(f"{API_URL}/dashboard/premium?user_id={user_id}", allow_redirects=False)
    assert r.status_code == expected_status

# --- Simulación de Alerta Multilingüe ---
@pytest.mark.parametrize("lang,expected_text", [
    ("es", "ha subido fotos nuevas"),
    ("pt", "enviou novas fotos"),
    ("en", "uploaded new photos"),
])
def test_alerta_multilingue(lang, expected_text):
    """Simula un cambio en la competencia y verifica que la alerta aparece en el dashboard en el idioma correcto."""
    # Simula trigger de alerta en backend
    payload = {
        "user_id": "premium-user-demo",
        "lang": lang,
        "competitor": "Competidor QA",
        "change": "photos",
        "delta": 7
    }
    r = requests.post(f"{API_URL}/api/alerts/simulate", json=payload)
    assert r.status_code == 200
    # Ahora consulta el dashboard
    r2 = requests.get(f"{API_URL}/dashboard/premium?user_id=premium-user-demo&lang={lang}")
    assert r2.status_code == 200
    assert expected_text in r2.text
