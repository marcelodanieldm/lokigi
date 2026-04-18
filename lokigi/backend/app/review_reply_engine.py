from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0


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
