from __future__ import annotations

from dataclasses import dataclass
import logging
import re
from typing import Any

import httpx
from langdetect import DetectorFactory, LangDetectException, detect

from .config import settings

DetectorFactory.seed = 0


logger = logging.getLogger(__name__)


SENSITIVE_TERMS = {
    "es": ["demanda", "abogado", "legal", "fraude", "estafa", "acoso", "discrimin"],
    "en": ["lawsuit", "lawyer", "legal", "fraud", "scam", "harassment", "discrimin"],
    "generic": ["police", "fiscalia", "tribunal", "court", "abuse", "racist"],
}


@dataclass
class ReviewReplyDecision:
    action: str
    detected_language: str
    reason: str
    public_reply: str
    alert_priority: str
    alert_category: str
    alert_summary: str
    alert_next_step: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "detected_language": self.detected_language,
            "reason": self.reason,
            "public_reply": self.public_reply,
            "internal_alert": {
                "priority": self.alert_priority,
                "category": self.alert_category,
                "summary": self.alert_summary,
                "recommended_next_step": self.alert_next_step,
            },
        }


def _detect_language(review_text: str) -> str:
    text = (review_text or "").strip()
    if len(text) < 8:
        return "es"

    try:
        lang = detect(text)
        return lang if lang else "es"
    except LangDetectException:
        return "es"


def _has_sensitive_content(review_text: str) -> bool:
    text = (review_text or "").lower()
    if not text:
        return False

    terms = SENSITIVE_TERMS["generic"] + SENSITIVE_TERMS["es"] + SENSITIVE_TERMS["en"]
    return any(term in text for term in terms)


def _template_high_rating(language: str, business_name: str, author_name: str) -> str:
    if language.startswith("es"):
        return (
            f"Muchas gracias, {author_name}, por tu reseña. En {business_name} nos alegra saber que tu experiencia fue positiva. "
            "Te esperamos nuevamente."
        )
    if language.startswith("pt"):
        return (
            f"Muito obrigado, {author_name}, pela sua avaliação. Na {business_name}, ficamos felizes em saber que sua experiência foi positiva. "
            "Esperamos você novamente."
        )
    if language.startswith("fr"):
        return (
            f"Merci beaucoup, {author_name}, pour votre avis. Chez {business_name}, nous sommes ravis de savoir que votre expérience a été positive. "
            "Au plaisir de vous revoir."
        )
    return (
        f"Thank you so much, {author_name}, for your review. At {business_name}, we are glad to hear your experience was positive. "
        "We look forward to welcoming you again."
    )


def _template_mid_rating(language: str, business_name: str, author_name: str) -> str:
    if language.startswith("es"):
        return (
            f"Gracias, {author_name}, por compartir tu experiencia con {business_name}. "
            "Valoramos tus comentarios y seguiremos mejorando para ofrecerte un mejor servicio."
        )
    return (
        f"Thank you, {author_name}, for sharing your experience with {business_name}. "
        "We value your feedback and will keep improving our service."
    )


# ── Tone-based reply templates ────────────────────────────────────────────────

def _generate_reply_cercano(
    language: str,
    business_name: str,
    author_name: str,
    rating: int,
) -> str:
    """Cercano (Close/Friendly): Casual, warm, personal tone."""
    if language.startswith("es"):
        if rating > 4:
            return (
                f"¡Qué alegría, {author_name}! 😊 Tu reseña nos hizo el día. "
                f"En {business_name} nos encanta saber que la pasaste bien. "
                "¡Vuelve pronto, te extrañaremos!"
            )
        return (
            f"Hola {author_name}, gracias por tu feedback. "
            f"En {business_name} siempre buscamos mejorar y tus comentarios nos ayudan mucho. "
            "¡Esperamos verte de nuevo pronto!"
        )
    if language.startswith("pt"):
        if rating > 4:
            return (
                f"Que alegria, {author_name}! 😊 Sua avaliação fez nosso dia. "
                f"Na {business_name}, adoramos saber que você se divertiu. "
                "Volte logo, você vai fazer falta!"
            )
        return (
            f"Oi {author_name}, obrigado pelo feedback. "
            f"Na {business_name}, sempre buscamos melhorar e seus comentários nos ajudam muito. "
            "Esperamos vê-lo em breve!"
        )
    # English friendly
    if rating > 4:
        return (
            f"What a joy, {author_name}! 😊 Your review made our day. "
            f"At {business_name}, we love knowing you had a great time. "
            "Come back soon, we'll miss you!"
        )
    return (
        f"Hi {author_name}, thanks for the feedback! "
        f"At {business_name}, we're always looking to improve, and your thoughts really help. "
        "Hope to see you again soon!"
    )


def _generate_reply_formal(
    language: str,
    business_name: str,
    author_name: str,
    rating: int,
) -> str:
    """Formal: Professional, corporate, polished tone."""
    if language.startswith("es"):
        if rating > 4:
            return (
                f"Estimado/a {author_name}, agradecemos sinceramente su valiosa reseña. "
                f"En {business_name}, nos complace confirmar que su experiencia fue satisfactoria. "
                "Confiamos en contar con su preferencia en futuras ocasiones."
            )
        return (
            f"Estimado/a {author_name}, apreciamos sus comentarios sobre {business_name}. "
            "Consideramos cada observación como una oportunidad de mejora y perfeccionamiento de nuestros servicios. "
            "Le invitamos a visitarnos nuevamente."
        )
    if language.startswith("pt"):
        if rating > 4:
            return (
                f"Prezado/a {author_name}, agradecemos sinceramente sua valiosa avaliação. "
                f"Em {business_name}, ficamos satisfeitos em confirmar que sua experiência foi positiva. "
                "Confiamos em contar com sua preferência em futuras ocasiões."
            )
        return (
            f"Prezado/a {author_name}, apreciamos seus comentários sobre {business_name}. "
            "Consideramos cada observação como uma oportunidade de melhoria e aperfeiçoamento de nossos serviços. "
            "Convidamos você a nos visitar novamente."
        )
    # English formal
    if rating > 4:
        return (
            f"Dear {author_name}, we sincerely appreciate your valued review. "
            f"At {business_name}, we are pleased to confirm that your experience was satisfactory. "
            "We look forward to serving you again."
        )
    return (
        f"Dear {author_name}, we appreciate your feedback regarding {business_name}. "
        "We view each observation as an opportunity for continuous improvement. "
        "We would welcome the opportunity to serve you again."
    )


def _generate_reply_moderno(
    language: str,
    business_name: str,
    author_name: str,
    rating: int,
) -> str:
    """Moderno (Modern): Contemporary, upbeat, dynamic tone."""
    if language.startswith("es"):
        if rating > 4:
            return (
                f"{author_name}, ¡gracias! Tu review es fuego. 🔥 "
                f"En {business_name} nos encanta cuando nuestro trabajo genera impacto. "
                "Seguiremos dándola al máximo. ¡Nos vemos!"
            )
        return (
            f"{author_name}, gracias por tomar el tiempo. 🙌 "
            f"En {business_name} estamos en constante evolución y tu feedback nos ayuda a llegar lejos. "
            "¡Nos vemos pronto!"
        )
    if language.startswith("pt"):
        if rating > 4:
            return (
                f"{author_name}, valeu! Sua review é top. 🔥 "
                f"Na {business_name}, a gente curte quando nosso trabalho faz impacto. "
                "Vamos seguir dando o melhor. Até breve!"
            )
        return (
            f"{author_name}, valeu por investir tempo com a gente. 🙌 "
            f"Na {business_name} estamos sempre evoluindo e seu feedback nos ajuda muito. "
            "Te vejo em breve!"
        )
    # English modern
    if rating > 4:
        return (
            f"{author_name}, thanks! Your review is fire. 🔥 "
            f"At {business_name}, we love seeing our work make an impact. "
            "We'll keep bringing our best. See you soon!"
        )
    return (
        f"{author_name}, thanks for the real talk. 🙌 "
        f"At {business_name}, we're always evolving and your feedback helps us grow. "
        "Catch you soon!"
    )


def build_dynamic_review_prompt(
    *,
    tone: str,
    review_text: str,
    business_name: str,
    author_name: str,
) -> str:
    safe_tone = (tone or "cercano").strip() or "cercano"
    safe_business_name = (business_name or "Negocio").strip() or "Negocio"
    safe_author_name = (author_name or "").strip()
    reviewer_line = safe_author_name if safe_author_name else "No disponible"
    return (
        f"Responde a esta reseña de Google Maps. El tono debe ser {safe_tone}. "
        "La respuesta debe ser corta, agradecer por nombre si está disponible y no usar frases genéricas de robot.\n\n"
        f"Negocio: {safe_business_name}\n"
        f"Autor: {reviewer_line}\n"
        f"Reseña: {review_text.strip() or '(sin comentario)'}\n\n"
        "Devuelve únicamente el texto final de la respuesta."
    )


def _clean_llm_reply(raw_text: str) -> str:
    text = (raw_text or "").strip()
    text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
    text = re.sub(r'```$', '', text).strip()
    return text.strip('"').strip()


def _call_review_reply_llm(prompt: str) -> str:
    endpoint = settings.review_reply_llm_api_base.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.review_reply_llm_model,
        "temperature": 0.3,
        "messages": [
            {
                "role": "system",
                "content": "Eres un asistente de reputación para Google Maps. Devuelve solo el texto final de la respuesta.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.review_reply_llm_api_key}",
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
    )
    return _clean_llm_reply(content)


def generate_reply_by_tone(
    *,
    tone: str,
    review_text: str,
    stars: int | None,
    business_name: str,
    author_name: str,
) -> str:
    """Generate a reply based on the selected tone.
    
    Args:
        tone: One of 'cercano', 'formal', 'moderno'
        review_text: The original review text
        stars: Rating (1-5)
        business_name: Name of the business
        author_name: Name of the review author
        
    Returns:
        Generated reply string
    """
    language = _detect_language(review_text)
    safe_business_name = (business_name or "our business").strip() or "our business"
    safe_author_name = (author_name or "there").strip() or "there"
    rating = int(stars or 0)
    
    tone_lower = (tone or "cercano").lower().strip()

    if settings.review_reply_llm_enabled and settings.review_reply_llm_api_key:
        prompt = build_dynamic_review_prompt(
            tone=tone_lower,
            review_text=review_text,
            business_name=safe_business_name,
            author_name="" if safe_author_name == "there" else safe_author_name,
        )
        try:
            llm_reply = _call_review_reply_llm(prompt)
            if llm_reply:
                return llm_reply
        except Exception:
            logger.exception("Review reply LLM generation failed; using local fallback templates")
    
    if tone_lower == "formal":
        return _generate_reply_formal(language, safe_business_name, safe_author_name, rating)
    elif tone_lower == "moderno":
        return _generate_reply_moderno(language, safe_business_name, safe_author_name, rating)
    else:  # Default to cercano
        return _generate_reply_cercano(language, safe_business_name, safe_author_name, rating)


def generate_review_reply_decision(
    *,
    review_text: str,
    stars: int | None,
    business_name: str,
    author_name: str,
) -> dict[str, Any]:
    language = _detect_language(review_text)
    safe_business_name = (business_name or "our business").strip() or "our business"
    safe_author_name = (author_name or "there").strip() or "there"
    rating = int(stars or 0)

    if rating < 3:
        return ReviewReplyDecision(
            action="ALERT",
            detected_language=language,
            reason="Low rating policy: automatic reply disabled.",
            public_reply="",
            alert_priority="HIGH",
            alert_category="LOW_RATING",
            alert_summary=f"Low rating detected ({rating} stars) for review from {safe_author_name}.",
            alert_next_step="Open a support ticket and assign the review to customer success for manual handling.",
        ).to_dict()

    if _has_sensitive_content(review_text):
        return ReviewReplyDecision(
            action="ALERT",
            detected_language=language,
            reason="Sensitive content detected.",
            public_reply="",
            alert_priority="HIGH",
            alert_category="SENSITIVE_CONTENT",
            alert_summary=f"Sensitive language detected in review from {safe_author_name}.",
            alert_next_step="Escalate to operations or legal reviewer before any public response.",
        ).to_dict()

    if rating > 4:
        return ReviewReplyDecision(
            action="AUTO_REPLY",
            detected_language=language,
            reason="High rating: gratitude auto-reply enabled.",
            public_reply=_template_high_rating(language, safe_business_name, safe_author_name),
            alert_priority="LOW",
            alert_category="OTHER",
            alert_summary="No alert required.",
            alert_next_step="None",
        ).to_dict()

    return ReviewReplyDecision(
        action="AUTO_REPLY",
        detected_language=language,
        reason="Mid rating: professional auto-reply enabled.",
        public_reply=_template_mid_rating(language, safe_business_name, safe_author_name),
        alert_priority="LOW",
        alert_category="OTHER",
        alert_summary="No alert required.",
        alert_next_step="None",
    ).to_dict()
