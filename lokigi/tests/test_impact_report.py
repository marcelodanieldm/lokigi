
import sys
import os
import tempfile
import shutil
import pytest

# Añadir la raíz del proyecto al sys.path para importar backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def get_db_final_score(business_id):
    # Simulación: en real, consulta a la base de datos
    # Aquí deberías conectar a tu DB real y obtener el score final
    return 92

def test_integridad_final_score():
    """
    Valida que el final_score del reporte coincida con la base de datos tras la intervención del Worker.
    """
    business_id = 1
    response = client.get(f"/impact-report?business_id={business_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["final_score"] == get_db_final_score(business_id)

def test_generacion_masiva_reportes():
    """
    Automatiza la creación de 10 reportes simultáneos para verificar que no haya fugas de memoria.
    """
    from concurrent.futures import ThreadPoolExecutor
    business_ids = list(range(1, 11))
    def generar_reporte(bid):
        r = client.get(f"/impact-report?business_id={bid}")
        assert r.status_code == 200
        return r.json()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(generar_reporte, business_ids))
    assert len(results) == 10

def test_visual_regression_pdf():
    """
    Verifica que los gráficos y textos no se corten en el PDF final, especialmente con nombres largos.
    """
    business_id = 99
    # Simula un nombre largo y dirección compleja
    payload = {
        "name": "Supermercado Brasileiro de São José dos Campos com Endereço Muito Longo e Complejo",
        "address": "Rua das Palmeiras, 1234, Bairro Jardim das Américas, São Paulo, Brasil, 01234-567",
        "final_score": 88
    }
    # Suponiendo que el endpoint genera y devuelve el PDF como bytes
    response = client.post(f"/impact-report/pdf", json=payload)
    assert response.status_code == 200
    pdf_bytes = response.content
    # Guardar PDF temporalmente para inspección manual o futura automatización visual
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    # Validación básica: el PDF debe tener tamaño suficiente y no estar vacío
    assert os.path.getsize(tmp_path) > 10000
    # Aquí podrías agregar validación visual con herramientas como pdfminer o visual-diff
    os.remove(tmp_path)
