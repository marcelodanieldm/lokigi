from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.config import settings


FOCUS_LABELS = {
    "service": "servicio",
    "product": "producto",
    "speed": "rapidez",
    "staff": "equipo",
    "cleanliness": "limpieza",
    "atmosphere": "ambiente",
    "pricing": "precio",
    "consistency": "consistencia",
    "other": "operacion",
}


FOCUS_KEYWORDS = {
    "service": ["servicio", "atencion", "trato", "experiencia", "atendieron"],
    "product": ["cafe", "comida", "plato", "producto", "sabor", "calidad"],
    "speed": ["rapido", "lento", "espera", "tard", "demora", "tiempo"],
    "staff": ["personal", "staff", "equipo", "mesero", "empleado"],
    "cleanliness": ["limpio", "sucio", "higiene", "limpieza"],
    "atmosphere": ["ambiente", "musica", "ruido", "comod", "decoracion"],
    "pricing": ["precio", "caro", "barato", "costoso", "valor"],
    "consistency": ["siempre", "otra vez", "constante", "igual", "inconsistente"],
}


@dataclass(slots=True)
class StarterTipResult:
    tip_del_dia: str
    focus: str
    confidence: float
    evidence_count: int
    supporting_signals: list[str]
    tone: str
    is_fallback: bool
    fallback_reason: str | None
    source: str

    def to_dict(self) -> dict:
        return {
            "tip_del_dia": self.tip_del_dia,
            "focus": self.focus,
            "confidence": round(self.confidence, 2),
            "evidence_count": self.evidence_count,
            "supporting_signals": self.supporting_signals,
            "tone": self.tone,
            "is_fallback": self.is_fallback,
            "fallback_reason": self.fallback_reason,
            "source": self.source,
        }


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _word_count(value: str) -> int:
    return len([w for w in (value or "").split() if w.strip()])


def _trim_tip_words(value: str, max_words: int = 32) -> str:
    words = [w for w in (value or "").split() if w.strip()]
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(".,;:!") + "."


def _extract_focus_scores(reviews: list[str]) -> dict[str, int]:
    scores = {key: 0 for key in FOCUS_KEYWORDS}
    for review in reviews:
        text = _normalize_text(review)
        for focus, keywords in FOCUS_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                scores[focus] += 1
    return scores


def _extract_supporting_signals(reviews: list[str], focus: str) -> list[str]:
    signals: list[str] = []
    keywords = FOCUS_KEYWORDS.get(focus, [])
    for review in reviews:
        text = review.strip()
        lowered = _normalize_text(text)
        if any(keyword in lowered for keyword in keywords):
            signals.append(_trim_tip_words(text, max_words=12))
        if len(signals) >= 3:
            break
    return signals


def _select_top_focus(reviews: list[str]) -> tuple[str, int]:
    scores = _extract_focus_scores(reviews)
    if not scores:
        return "other", 0
    top_focus = max(scores, key=scores.get)
    top_count = scores[top_focus]
    if top_count <= 0:
        return "other", 0
    return top_focus, top_count


def _has_sufficient_signal(reviews: list[str], evidence_count: int) -> bool:
    if len(reviews) < 4:
        return False
    return evidence_count >= 2


def build_lokigi_tip_prompt(
    *,
    business_name: str,
    business_type: str,
    location: str,
    reviews: list[str],
) -> str:
    lines = "\n".join(f"{i + 1}. {review}" for i, review in enumerate(reviews[:10]))
    return (
        "Eres el motor de insights de Lokigi para clientes Starter.\n\n"
        "Analiza las ultimas 10 resenas y genera un unico 'Tip del Dia' breve y accionable para el panel.\n"
        "Reglas: no inventes hechos, una sola frase, maximo 32 palabras, tono cercano-profesional, salida JSON valida.\n\n"
        "Devuelve solo este JSON:\n"
        "{\n"
        '  "tip_del_dia": "string",\n'
        '  "focus": "service|product|speed|staff|cleanliness|atmosphere|pricing|consistency|other",\n'
        '  "confidence": 0.0,\n'
        '  "evidence_count": 0,\n'
        '  "supporting_signals": ["string"],\n'
        '  "tone": "opportunity|warning|reinforcement"\n'
        "}\n\n"
        f"Contexto:\nNombre: {business_name}\nTipo: {business_type}\nUbicacion: {location}\n\n"
        f"Resenas:\n{lines}"
    )


def _build_no_signal_fallback() -> StarterTipResult:
    return StarterTipResult(
        tip_del_dia=(
            "Hoy enfocate en pedir una resena concreta al finalizar cada servicio:"
            " aumentar volumen reciente mejora visibilidad y te da mejor señal para recomendaciones mas precisas."
        ),
        focus="other",
        confidence=0.35,
        evidence_count=0,
        supporting_signals=[],
        tone="opportunity",
        is_fallback=True,
        fallback_reason="insufficient_signal",
        source="fallback",
    )


def _build_heuristic_tip(reviews: list[str], business_name: str) -> StarterTipResult:
    focus, evidence_count = _select_top_focus(reviews)
    signals = _extract_supporting_signals(reviews, focus)
    topic = FOCUS_LABELS.get(focus, "operacion")
    tone = "warning" if focus in {"speed", "pricing", "cleanliness"} else "reinforcement"

    if tone == "warning":
        tip = (
            f"Varios comentarios recientes apuntan a {topic}; define hoy una mejora puntual en {business_name} "
            "y verifica su impacto en las proximas respuestas para proteger tus 5 estrellas."
        )
    else:
        tip = (
            f"Tus ultimas resenas destacan {topic}; estandariza hoy esa practica en {business_name} "
            "para sostener consistencia y convertir mas clientes satisfechos en nuevas reseñas de 5 estrellas."
        )

    return StarterTipResult(
        tip_del_dia=_trim_tip_words(tip),
        focus=focus,
        confidence=min(0.9, 0.45 + (evidence_count / 10)),
        evidence_count=min(10, evidence_count),
        supporting_signals=signals,
        tone=tone,
        is_fallback=False,
        fallback_reason=None,
        source="heuristic",
    )


def _validate_llm_payload(payload: dict) -> StarterTipResult:
    tip = _trim_tip_words(str(payload.get("tip_del_dia", "")).strip())
    if not tip:
        raise ValueError("tip_del_dia is missing")

    focus = str(payload.get("focus", "other")).strip().lower() or "other"
    if focus not in FOCUS_LABELS:
        focus = "other"

    tone = str(payload.get("tone", "opportunity")).strip().lower() or "opportunity"
    if tone not in {"opportunity", "warning", "reinforcement"}:
        tone = "opportunity"

    confidence = float(payload.get("confidence", 0.6))
    confidence = max(0.0, min(1.0, confidence))

    evidence_count = int(payload.get("evidence_count", 1))
    evidence_count = max(0, min(10, evidence_count))

    raw_signals = payload.get("supporting_signals", [])
    signals: list[str] = []
    if isinstance(raw_signals, list):
        for item in raw_signals[:3]:
            txt = str(item).strip()
            if txt:
                signals.append(txt)

    return StarterTipResult(
        tip_del_dia=tip,
        focus=focus,
        confidence=confidence,
        evidence_count=evidence_count,
        supporting_signals=signals,
        tone=tone,
        is_fallback=False,
        fallback_reason=None,
        source="llm",
    )


def _call_openai_compatible(prompt: str) -> StarterTipResult:
    if not settings.tip_llm_api_key:
        raise ValueError("Missing tip LLM API key")

    endpoint = settings.tip_llm_api_base.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.tip_llm_model,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "Eres el motor de insights de Lokigi Starter. Devuelve solo JSON valido.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {settings.tip_llm_api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=20.0) as client:
        response = client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        body = response.json()

    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    parsed = json.loads(content)
    return _validate_llm_payload(parsed)


def generate_starter_tip(
    *,
    business_name: str,
    business_type: str,
    location: str,
    reviews: list[str],
) -> dict:
    clean_reviews = [review.strip() for review in reviews if review and review.strip()][:10]
    if not clean_reviews:
        result = _build_no_signal_fallback()
        output = result.to_dict()
        output.update(
            {
                "reviews_analyzed": 0,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model_provider": None,
                "model_name": None,
            }
        )
        return output

    focus, evidence_count = _select_top_focus(clean_reviews)
    if not _has_sufficient_signal(clean_reviews, evidence_count):
        result = _build_no_signal_fallback()
        output = result.to_dict()
        output.update(
            {
                "reviews_analyzed": len(clean_reviews),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model_provider": None,
                "model_name": None,
            }
        )
        return output

    if settings.tip_llm_enabled:
        try:
            prompt = build_lokigi_tip_prompt(
                business_name=business_name,
                business_type=business_type,
                location=location,
                reviews=clean_reviews,
            )
            llm_result = _call_openai_compatible(prompt)
            output = llm_result.to_dict()
            output.update(
                {
                    "reviews_analyzed": len(clean_reviews),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model_provider": "openai-compatible",
                    "model_name": settings.tip_llm_model,
                }
            )
            return output
        except Exception:
            # If model call fails, keep endpoint stable by returning heuristic output.
            pass

    heuristic = _build_heuristic_tip(clean_reviews, business_name)
    output = heuristic.to_dict()
    output.update(
        {
            "reviews_analyzed": len(clean_reviews),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_provider": None,
            "model_name": None,
            "focus": focus,
            "evidence_count": min(10, evidence_count),
        }
    )
    return output
