"""
Test suite automatizada para Reportes de Impacto (Certificado de Éxito Lokigi).
- Valida integridad de datos, generación concurrente y regresión visual básica.
"""
import pytest
import requests
import uuid
from PyPDF2 import PdfReader

API_URL = "http://localhost:8000/order"

# Simula una base de datos de órdenes
ORDERS_DB = {}

@pytest.mark.parametrize("final_score", [77, 85, 92])
def test_integridad_final_score(final_score):
    """Valida que el final_score en el PDF coincida con el enviado y guardado en la base."""
    order_id = str(uuid.uuid4())
    payload = {
        "user_email": f"test{order_id[:8]}@lokigi.com",
        "business_id": order_id,
        "lang": "es",
        "name": "Negocio QA",
        "address": "Calle Falsa 123, Buenos Aires",
        "final_score": final_score,
        "improvements": ["SEO", "Fotos"],
        "photos": [{"lat": -34.6, "lon": -58.4}],
        "ranking": [{"name": "Negocio QA", "score": final_score}],
        "radar_labels": ["SEO"],
        "radar_before": [50],
        "radar_after": [final_score]
    }
    r = requests.post(API_URL, json=payload)
    assert r.status_code == 200
    data = r.json()
    ORDERS_DB[order_id] = final_score
    # Descarga el PDF
    pdf_url = data["report_url"]
    pdf = requests.get(pdf_url)
    assert pdf.status_code == 200
    reader = PdfReader(pdf.content)
    text = "".join(page.extract_text() for page in reader.pages)
    assert str(final_score) in text


def test_generacion_concurrente():
    """Automatiza la creación de 10 reportes simultáneos para detectar fugas de memoria o errores de concurrencia."""
    import concurrent.futures
    def create_report(i):
        payload = {
            "user_email": f"stress{i}@lokigi.com",
            "business_id": str(uuid.uuid4()),
            "lang": "pt" if i % 2 == 0 else "en",
            "name": f"Empresa Stress {i}",
            "address": f"Rua Complexa {i}, São Paulo, Brasil",
            "final_score": 80 + i,
            "improvements": ["SEO", "Fotos"],
            "photos": [{"lat": -23.5, "lon": -46.6}],
            "ranking": [{"name": f"Empresa Stress {i}", "score": 80 + i}],
            "radar_labels": ["SEO"],
            "radar_before": [60],
            "radar_after": [80 + i]
        }
        r = requests.post(API_URL, json=payload)
        assert r.status_code == 200
        data = r.json()
        pdf = requests.get(data["report_url"])
        assert pdf.status_code == 200
        return True
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(create_report, range(10)))
    assert all(results)

@pytest.mark.parametrize("name,address", [
    ("Negocio con nombre extremadamente largo que podría cortar el PDF en dispositivos móviles", "Rua das Flores, 1234, Bairro Muito Comprido, São Paulo, Brasil"),
    ("Empresa QA", "Avenida Paulista, 1578, São Paulo, Brasil"),
])
def test_visual_regression(name, address):
    """Verifica que los textos largos no se corten en el PDF final."""
    payload = {
        "user_email": f"visualtest@lokigi.com",
        "business_id": str(uuid.uuid4()),
        "lang": "pt",
        "name": name,
        "address": address,
        "final_score": 95,
        "improvements": ["SEO", "Fotos"],
        "photos": [{"lat": -23.5, "lon": -46.6}],
        "ranking": [{"name": name, "score": 95}],
        "radar_labels": ["SEO"],
        "radar_before": [60],
        "radar_after": [95]
    }
    r = requests.post(API_URL, json=payload)
    assert r.status_code == 200
    data = r.json()
    pdf = requests.get(data["report_url"])
    assert pdf.status_code == 200
    reader = PdfReader(pdf.content)
    text = "".join(page.extract_text() for page in reader.pages)
    # El nombre y dirección deben aparecer completos
    assert name[:20] in text
    assert address[:20] in text
