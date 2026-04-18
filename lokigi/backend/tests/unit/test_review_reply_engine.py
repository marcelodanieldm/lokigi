from app.review_reply_engine import generate_review_reply_decision


def test_low_rating_triggers_alert_and_no_public_reply() -> None:
    decision = generate_review_reply_decision(
        review_text="Mala experiencia, no volveria.",
        stars=2,
        business_name="Lokigi",
        author_name="Carla",
    )

    assert decision["action"] == "ALERT"
    assert decision["public_reply"] == ""
    assert decision["internal_alert"]["category"] == "LOW_RATING"


def test_high_rating_generates_thank_you_with_business_and_author() -> None:
    decision = generate_review_reply_decision(
        review_text="Excelente servicio, muy recomendado.",
        stars=5,
        business_name="Lokigi",
        author_name="Marcela",
    )

    assert decision["action"] == "AUTO_REPLY"
    assert "Lokigi" in decision["public_reply"]
    assert "Marcela" in decision["public_reply"]


def test_english_review_detects_en_language() -> None:
    decision = generate_review_reply_decision(
        review_text="Great service and very fast support, thank you for the amazing help.",
        stars=4,
        business_name="Lokigi",
        author_name="John",
    )

    assert decision["detected_language"].startswith("en")


def test_mid_rating_sensitive_content_triggers_alert() -> None:
    decision = generate_review_reply_decision(
        review_text="This is fraud and we will contact a lawyer.",
        stars=4,
        business_name="Lokigi",
        author_name="Alex",
    )

    assert decision["action"] == "ALERT"
    assert decision["internal_alert"]["category"] == "SENSITIVE_CONTENT"
    assert decision["public_reply"] == ""


def test_mid_rating_non_sensitive_generates_professional_reply() -> None:
    decision = generate_review_reply_decision(
        review_text="Buen servicio en general, aunque hubo un poco de demora.",
        stars=3,
        business_name="Lokigi",
        author_name="Sofia",
    )

    assert decision["action"] == "AUTO_REPLY"
    assert decision["public_reply"]
