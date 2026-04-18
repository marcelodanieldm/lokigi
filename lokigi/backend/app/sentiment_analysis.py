"""sentiment_analysis.py
Lexicon-based concept extraction for monthly sentiment reports.

Strategy
--------
* Polarity is derived from the star rating, which is ground truth:
    - stars 4-5  → positive context
    - stars 1-2  → negative context
    - stars 3    → neutral (skipped to avoid noisy attribution)
* For each review, every concept whose keywords appear in the text is
  counted once per polarity bucket (no double-counting per review).
* Top-N concepts are returned as structured JSON ready for a bar chart.

No external ML libraries required – pure Python + stdlib only.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Concept lexicon  (bilingual ES / EN, case-insensitive substring matching)
# ---------------------------------------------------------------------------
# Each entry:  "Display label"  →  {"es": [...keywords...], "en": [...]}
# A keyword matches if it appears as a word (word-boundary aware).
# ---------------------------------------------------------------------------

CONCEPT_LEXICON: dict[str, dict[str, list[str]]] = {
    "atención al cliente": {
        "es": ["atención", "atencion", "trato", "amable", "amabilidad", "personal",
                "empleado", "empleada", "trabajador", "asesor", "asesora"],
        "en": ["staff", "employee", "attention", "friendly", "helpful", "kind", "polite",
               "courteous", "service"],
    },
    "rapidez": {
        "es": ["rápido", "rapido", "rápida", "rapida", "veloz", "pronto",
               "inmediato", "ágil", "agil", "eficiente", "eficiencia"],
        "en": ["fast", "quick", "speedy", "prompt", "efficient", "swift", "immediate"],
    },
    "tiempo de espera": {
        "es": ["espera", "tardaron", "tardé", "tarde", "demora", "demoraron",
               "lento", "lenta", "lentitud", "esperar", "cola", "fila"],
        "en": ["wait", "waiting", "slow", "delay", "took long", "queue", "line"],
    },
    "precio / costo": {
        "es": ["precio", "precios", "caro", "cara", "costoso", "costosa",
               "económico", "economico", "barato", "barata", "tarifa",
               "costo", "cobro", "cobran", "factura", "facturación"],
        "en": ["price", "prices", "expensive", "cheap", "affordable",
               "cost", "overpriced", "pricey", "fee", "billing"],
    },
    "limpieza": {
        "es": ["limpio", "limpia", "limpieza", "sucio", "sucia", "suciedad",
               "higiene", "higiénico", "higienico"],
        "en": ["clean", "cleanliness", "dirty", "hygiene", "filthy", "spotless", "tidy"],
    },
    "calidad del producto": {
        "es": ["calidad", "producto", "productos", "fresco", "fresca",
               "mal estado", "defectuoso", "defectuosa", "excelente", "pésimo",
               "pesimo", "pésima", "pesima"],
        "en": ["quality", "product", "products", "fresh", "defective",
               "excellent", "poor quality", "great quality", "terrible"],
    },
    "ambiente / local": {
        "es": ["ambiente", "local", "lugar", "espacio", "cómodo", "comodo",
               "incómodo", "incomodo", "decoración", "decoracion",
               "bonito", "bonita", "agradable", "desagradable"],
        "en": ["atmosphere", "ambiance", "place", "cozy", "comfortable",
               "location", "decor", "pleasant", "unpleasant", "nice"],
    },
    "comunicación": {
        "es": ["comunica", "comunicación", "comunicacion", "responde", "respuesta",
               "contacto", "llamada", "explicó", "explico", "informó", "informo",
               "atendieron", "contestaron"],
        "en": ["communicate", "communication", "response", "contact",
               "explained", "informed", "answered", "replied"],
    },
    "variedad de opciones": {
        "es": ["variedad", "opciones", "opción", "opcion", "menú", "menu",
               "selección", "seleccion", "alternativas", "surtido"],
        "en": ["variety", "options", "menu", "selection", "choice", "range", "assortment"],
    },
    "horario": {
        "es": ["horario", "horarios", "abierto", "cerrado", "puntual",
               "puntualidad", "temprano", "tarde", "disponible"],
        "en": ["hours", "schedule", "open", "closed", "punctual",
               "on time", "late", "early", "available"],
    },
    "cumplimiento / entrega": {
        "es": ["prometió", "prometio", "cumplió", "cumplio", "incumplió",
               "incumplio", "entrega", "entregaron", "prometido", "garantía", "garantia"],
        "en": ["promise", "delivery", "guarantee", "commitment",
               "fulfilled", "delivered", "honored"],
    },
    "estacionamiento": {
        "es": ["estacionamiento", "parking", "aparcar", "estacionar", "parqueo"],
        "en": ["parking", "park", "car park"],
    },
}

# Pre-compile all patterns once at import time
# Pattern: word-boundary match, case-insensitive
_COMPILED: dict[str, list[re.Pattern[str]]] = {}
for _concept, _langs in CONCEPT_LEXICON.items():
    patterns: list[re.Pattern[str]] = []
    for _keywords in _langs.values():
        for _kw in _keywords:
            # Escape and wrap in word boundaries (\b)
            patterns.append(re.compile(r"\b" + re.escape(_kw) + r"\b", re.IGNORECASE))
    _COMPILED[_concept] = patterns


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass
class ConceptHit:
    concept: str
    count: int
    pct: float


@dataclass
class SentimentReport:
    year: int
    month: int
    location_id: str
    total_reviews_analyzed: int
    positive_reviews: int
    negative_reviews: int
    positive_concepts: list[ConceptHit] = field(default_factory=list)
    negative_concepts: list[ConceptHit] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        pos = [{"concept": h.concept, "count": h.count, "pct": h.pct}
               for h in self.positive_concepts]
        neg = [{"concept": h.concept, "count": h.count, "pct": h.pct}
               for h in self.negative_concepts]

        # Merge labels for bar chart (positives first, then negatives)
        pos_labels = [h["concept"] for h in pos]
        neg_labels = [h["concept"] for h in neg]
        all_labels = pos_labels + [l for l in neg_labels if l not in pos_labels]

        pos_values = [next((h["count"] for h in pos if h["concept"] == l), 0)
                      for l in all_labels]
        neg_values = [next((h["count"] for h in neg if h["concept"] == l), 0)
                      for l in all_labels]

        return {
            "period": {"year": self.year, "month": self.month},
            "location_id": self.location_id,
            "total_reviews_analyzed": self.total_reviews_analyzed,
            "positive_reviews": self.positive_reviews,
            "negative_reviews": self.negative_reviews,
            "positive_concepts": pos,
            "negative_concepts": neg,
            "chart_data": {
                "labels": all_labels,
                "positive": pos_values,
                "negative": neg_values,
            },
        }


# ---------------------------------------------------------------------------
# Extraction logic
# ---------------------------------------------------------------------------

def _matches(text: str, concept: str) -> bool:
    """Return True if any keyword for the concept appears in text."""
    for pattern in _COMPILED[concept]:
        if pattern.search(text):
            return True
    return False


def _extract_concepts(text: str) -> list[str]:
    """Return list of concept labels found in text (deduplicated)."""
    text = (text or "").strip()
    if not text:
        return []
    return [concept for concept in CONCEPT_LEXICON if _matches(text, concept)]


def analyze_monthly_sentiment(
    reviews: list[dict[str, Any]],
    *,
    year: int,
    month: int,
    location_id: str,
    top_n: int = 3,
) -> SentimentReport:
    """Compute concept-level sentiment for a list of review dicts.

    Each review dict must have:
        - ``comment``: str | None
        - ``rating``:  int | None  (1-5 stars)

    Stars 4-5 → positive context.
    Stars 1-2 → negative context.
    Stars 3   → neutral, skipped.
    """
    positive_counter: Counter[str] = Counter()
    negative_counter: Counter[str] = Counter()
    positive_reviews = 0
    negative_reviews = 0

    for review in reviews:
        stars = int(review.get("rating") or 0)
        text = (review.get("comment") or "").strip()

        if stars >= 4:
            positive_reviews += 1
            for concept in _extract_concepts(text):
                positive_counter[concept] += 1
        elif stars <= 2 and stars > 0:
            negative_reviews += 1
            for concept in _extract_concepts(text):
                negative_counter[concept] += 1
        # stars == 3 or stars == 0 → skip

    total = positive_reviews + negative_reviews

    def _build_hits(counter: Counter[str], base: int) -> list[ConceptHit]:
        return [
            ConceptHit(
                concept=concept,
                count=count,
                pct=round(count / base * 100, 1) if base else 0.0,
            )
            for concept, count in counter.most_common(top_n)
        ]

    return SentimentReport(
        year=year,
        month=month,
        location_id=location_id,
        total_reviews_analyzed=total,
        positive_reviews=positive_reviews,
        negative_reviews=negative_reviews,
        positive_concepts=_build_hits(positive_counter, positive_reviews),
        negative_concepts=_build_hits(negative_counter, negative_reviews),
    )
