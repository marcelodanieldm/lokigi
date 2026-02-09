# test_gemini_audit.py
"""
QA Automation para Lokigi: Stress Test de Inteligencia y Localización

- Prueba de Idioma: Negocio en Lisboa debe recibir respuesta en Portugués de Portugal.
- Prueba de Lógica: Si el negocio tiene 5 estrellas pero pocas fotos, la IA debe priorizar contenido visual.
- Prueba de Velocidad: El reporte debe generarse en menos de 4 segundos.
"""
import time
import requests

API_URL = "http://localhost:8000/audit/gemini_prompt"

def test_idioma_portugal():
    """Verifica que la respuesta sea en Portugués de Portugal para Lisboa."""
    payload = {
        "score": 90,
        "rubro": "Restaurante",
        "competencia": "5 restaurantes en 1km con 4.7 estrellas",
        "fallo": "Poucas fotos dos pratos",
        "pais": "PT",
        "lang": "pt"
    }
    start = time.time()
    resp = requests.post(API_URL, json=payload, timeout=8)
    elapsed = time.time() - start
    assert resp.status_code == 200, f"Status inesperado: {resp.status_code}"
    data = resp.json()
    # Prueba de idioma: buscar palabras típicas de Portugal
    assert any(word in data["QuickWin"].lower() for word in ["fotografias", "pratos", "negócio"]), "No parece portugués de Portugal"
    assert elapsed < 4, f"El reporte tardó demasiado: {elapsed:.2f}s"


def test_logica_prioriza_visual():
    """Verifica que la IA no recomiende mejorar reseñas si ya tiene 5 estrellas, pero sí contenido visual."""
    payload = {
        "score": 100,
        "rubro": "Peluquería",
        "competencia": "3 locales en 1km con 5 estrellas",
        "fallo": "Solo tiene 2 fotos subidas",
        "pais": "ES",
        "lang": "es"
    }
    resp = requests.post(API_URL, json=payload, timeout=8)
    data = resp.json()
    # No debe recomendar mejorar reseñas
    assert not any("reseña" in v.lower() for v in data.values()), "La IA recomendó mejorar reseñas innecesariamente"
    # Debe recomendar contenido visual
    assert any("foto" in v.lower() or "visual" in v.lower() for v in data.values()), "No recomendó contenido visual"

if __name__ == "__main__":
    print("Ejecutando pruebas QA para Lokigi...")
    test_idioma_portugal()
    print("✔ Prueba de idioma (Portugal) OK")
    test_logica_prioriza_visual()
    print("✔ Prueba de lógica (prioriza visual) OK")
    print("Todas las pruebas pasaron.")
