"""
Algoritmo de Lead Scoring Automático para Lokigi
Chief Data Officer: Selección y priorización de High-Value Targets
"""
import json
from typing import List, Dict
import re

# Tabla de valor de cliente por categoría
CLIENT_VALUE = {
    "Dentista": 5,
    "Abogado": 5,
    "Reformas": 4,
    "Clínica": 4,
    "Veterinaria": 4,
    "Gimnasio": 3,
    "Cafetería": 2,
    "Barbería": 2,
    "Tienda": 1
}

# Detección de idioma por país o dominio
def detect_lang(phone: str = "", website: str = "") -> str:
    if phone.startswith("+55") or ".br" in website:
        return "pt"
    if phone.startswith("+1") or ".us" in website or ".com" in website:
        return "en"
    if phone.startswith("+34") or ".es" in website:
        return "es"
    # Default: español
    return "es"


def lead_scoring(businesses: List[Dict]) -> List[Dict]:
    """
    businesses: lista de dicts con keys:
      - name, is_claimed, rating, last_review_days, category, phone, website
    Return: lista de High-Value Targets priorizados
    """
    filtered = []
    for b in businesses:
        if (
            not b.get("is_claimed", True)
            or b.get("rating", 5.0) < 4.0
            or b.get("last_review_days", 0) > 180
        ):
            filtered.append(b)
    # Priorización por ticket
    for b in filtered:
        b["score"] = CLIENT_VALUE.get(b.get("category", ""), 1)
        b["lang"] = detect_lang(b.get("phone", ""), b.get("website", ""))
    # Ordena por score descendente
    filtered.sort(key=lambda x: -x["score"])
    return filtered

if __name__ == "__main__":
    # Ejemplo de uso
    businesses = [
        {"name": "Dentista Smile", "is_claimed": False, "rating": 4.5, "last_review_days": 10, "category": "Dentista", "phone": "+34...", "website": "smile.es"},
        {"name": "Café Central", "is_claimed": True, "rating": 3.8, "last_review_days": 20, "category": "Cafetería", "phone": "+34...", "website": "cafecentral.com"},
        {"name": "Reformas Pro", "is_claimed": True, "rating": 4.2, "last_review_days": 200, "category": "Reformas", "phone": "+55...", "website": "reformaspro.com.br"},
        {"name": "Tienda X", "is_claimed": True, "rating": 4.5, "last_review_days": 30, "category": "Tienda", "phone": "+1...", "website": "tiendax.us"}
    ]
    targets = lead_scoring(businesses)
    print(json.dumps({"high_value_targets": targets}, ensure_ascii=False, indent=2))
