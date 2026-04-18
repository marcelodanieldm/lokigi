"""Unit tests for tone-based reply generation.

Tests the three tone variants: cercano, formal, moderno.
Validates multilingual support (ES, PT, EN) and rating awareness.
"""

import pytest
from app.review_reply_engine import (
    generate_reply_by_tone,
    _generate_reply_cercano,
    _generate_reply_formal,
    _generate_reply_moderno,
)


class TestToneCercano:
    """Test friendly/close tone generation."""

    def test_cercano_high_rating_spanish(self):
        """High rating should generate celebration message."""
        reply = _generate_reply_cercano("es", "Mi Negocio", "Juan", 5)
        assert "alegría" in reply or "alegria" in reply
        assert "Juan" in reply
        assert "Mi Negocio" in reply
        assert len(reply) > 30

    def test_cercano_mid_rating_spanish(self):
        """Mid rating should generate appreciation + improvement message."""
        reply = _generate_reply_cercano("es", "Mi Negocio", "María", 3)
        assert "gracias" in reply
        assert "María" in reply
        assert "mejora" in reply or "mejorar" in reply

    def test_cercano_high_rating_english(self):
        """English: high rating celebration."""
        reply = _generate_reply_cercano("en", "My Business", "John", 5)
        assert "joy" in reply or "great" in reply.lower()
        assert "John" in reply
        assert len(reply) > 30

    def test_cercano_portuguese(self):
        """Portuguese: should include Portuguese-specific phrases."""
        reply = _generate_reply_cercano("pt", "Meu Negócio", "Pedro", 5)
        assert "alegria" in reply or "alegria" in reply.lower()
        assert "Pedro" in reply
        assert len(reply) > 30

    def test_cercano_contains_emoji(self):
        """Friendly tone should include emojis for warmth."""
        reply = _generate_reply_cercano("es", "Business", "Alex", 5)
        # Check for emoji characters
        assert any(ord(c) > 127 for c in reply)  # Non-ASCII characters


class TestToneFormal:
    """Test professional/corporate tone generation."""

    def test_formal_high_rating_spanish(self):
        """High rating with formal tone."""
        reply = _generate_reply_formal("es", "Empresa", "Cliente", 5)
        assert "estimado" in reply or "estimada" in reply
        assert "sinceramente" in reply
        assert "Cliente" in reply
        assert len(reply) > 40

    def test_formal_mid_rating_spanish(self):
        """Mid rating formal response."""
        reply = _generate_reply_formal("es", "Empresa", "Cliente", 3)
        assert "apreciamos" in reply
        assert "mejora" in reply
        assert "Cliente" in reply

    def test_formal_high_rating_english(self):
        """English formal response."""
        reply = _generate_reply_formal("en", "Company", "Client", 5)
        assert "dear" in reply.lower()
        assert "sincerely" in reply.lower() or "appreciate" in reply.lower()
        assert "Client" in reply

    def test_formal_portuguese(self):
        """Portuguese formal response."""
        reply = _generate_reply_formal("pt", "Empresa", "Cliente", 5)
        assert "prezado" in reply or "prezada" in reply
        assert len(reply) > 40

    def test_formal_no_emoji(self):
        """Formal tone should be emoji-free."""
        reply = _generate_reply_formal("es", "Business", "Client", 5)
        # Should not have excessive emoji (may have formal symbols)
        emoji_count = sum(1 for c in reply if ord(c) > 127 and c not in "áéíóúñü")
        assert emoji_count < 3  # Allow a few accented chars, not many emojis


class TestToneModerno:
    """Test contemporary/dynamic tone generation."""

    def test_moderno_high_rating_spanish(self):
        """Modern tone with high rating."""
        reply = _generate_reply_moderno("es", "Startup", "Usuario", 5)
        assert "fuego" in reply or "top" in reply
        assert "Usuario" in reply
        assert len(reply) > 30

    def test_moderno_mid_rating_spanish(self):
        """Modern tone with mid rating."""
        reply = _generate_reply_moderno("es", "Startup", "Usuario", 3)
        assert "evolución" in reply or "evolucion" in reply
        assert "Usuario" in reply

    def test_moderno_high_rating_english(self):
        """English modern response."""
        reply = _generate_reply_moderno("en", "Startup", "User", 5)
        assert "fire" in reply.lower() or "great" in reply.lower()
        assert "User" in reply

    def test_moderno_portuguese(self):
        """Portuguese modern response."""
        reply = _generate_reply_moderno("pt", "Startup", "Usuário", 5)
        assert "top" in reply or "legal" in reply
        assert "Usuário" in reply

    def test_moderno_contains_casual_language(self):
        """Modern tone should use casual/slang terms."""
        reply = _generate_reply_moderno("es", "Business", "User", 5)
        # Look for casual markers
        assert any(word in reply.lower() for word in ["fuego", "top", "máximo", "maximo", "legítimo"])


class TestToneDispatcher:
    """Test the main dispatcher function."""

    def test_dispatcher_cercano(self):
        """Dispatcher correctly routes to cercano."""
        reply = generate_reply_by_tone(
            tone="cercano",
            review_text="¡Excelente servicio!",
            stars=5,
            business_name="Mi Negocio",
            author_name="Juan",
        )
        assert "Juan" in reply
        assert len(reply) > 20

    def test_dispatcher_formal(self):
        """Dispatcher correctly routes to formal."""
        reply = generate_reply_by_tone(
            tone="formal",
            review_text="Buen servicio",
            stars=5,
            business_name="Empresa",
            author_name="Cliente",
        )
        assert "Cliente" in reply
        assert "estimado" in reply.lower() or "dear" in reply.lower()

    def test_dispatcher_moderno(self):
        """Dispatcher correctly routes to moderno."""
        reply = generate_reply_by_tone(
            tone="moderno",
            review_text="Muy bueno",
            stars=5,
            business_name="Startup",
            author_name="User",
        )
        assert "User" in reply

    def test_dispatcher_default_to_cercano(self):
        """Unknown tone defaults to cercano."""
        reply = generate_reply_by_tone(
            tone="UNKNOWN_TONE",
            review_text="Review",
            stars=5,
            business_name="Business",
            author_name="Author",
        )
        # Should be cercano (friendly) format
        assert "Author" in reply
        assert len(reply) > 20

    def test_dispatcher_case_insensitive(self):
        """Tone should be case-insensitive."""
        reply1 = generate_reply_by_tone(
            tone="FORMAL",
            review_text="Test",
            stars=5,
            business_name="Business",
            author_name="Author",
        )
        reply2 = generate_reply_by_tone(
            tone="formal",
            review_text="Test",
            stars=5,
            business_name="Business",
            author_name="Author",
        )
        assert reply1 == reply2

    def test_dispatcher_with_none_values(self):
        """Should handle None values gracefully."""
        reply = generate_reply_by_tone(
            tone=None,
            review_text="Review",
            stars=None,
            business_name=None,
            author_name=None,
        )
        assert len(reply) > 0
        assert isinstance(reply, str)

    def test_dispatcher_with_empty_strings(self):
        """Should handle empty strings gracefully."""
        reply = generate_reply_by_tone(
            tone="",
            review_text="",
            stars=0,
            business_name="",
            author_name="",
        )
        assert len(reply) > 0
        assert isinstance(reply, str)


class TestMultilingualSupport:
    """Test language detection and multilingual responses."""

    def test_spanish_detection(self):
        """Spanish text should generate Spanish reply."""
        reply = generate_reply_by_tone(
            tone="cercano",
            review_text="Excelente atención y servicio de calidad",
            stars=5,
            business_name="Negocio",
            author_name="Cliente",
        )
        # Should be in Spanish
        assert any(word in reply for word in ["alegría", "alegria", "gracias", "vuelve"])

    def test_english_detection(self):
        """English text should generate English reply."""
        reply = generate_reply_by_tone(
            tone="cercano",
            review_text="Excellent service and quality",
            stars=5,
            business_name="Business",
            author_name="Client",
        )
        # Should be in English
        assert any(word in reply.lower() for word in ["thank", "great", "joy"])


class TestRatingAwareness:
    """Test that replies vary based on rating."""

    def test_same_tone_different_ratings(self):
        """Same tone should generate different messages for high vs mid ratings."""
        high = generate_reply_by_tone(
            tone="cercano",
            review_text="Excelente",
            stars=5,
            business_name="Biz",
            author_name="User",
        )
        mid = generate_reply_by_tone(
            tone="cercano",
            review_text="Bueno",
            stars=3,
            business_name="Biz",
            author_name="User",
        )
        # Replies should be different
        assert high != mid
        # High rating should have celebratory tone
        assert "alegría" in high or "alegria" in high or "joy" in high.lower()

    def test_formal_high_vs_mid(self):
        """Formal tone: high and mid should differ."""
        high = generate_reply_by_tone(
            tone="formal",
            review_text="Excellente",
            stars=5,
            business_name="Biz",
            author_name="User",
        )
        mid = generate_reply_by_tone(
            tone="formal",
            review_text="Ok",
            stars=3,
            business_name="Biz",
            author_name="User",
        )
        assert high != mid


class TestOutputValidation:
    """Test that outputs are valid and properly formatted."""

    def test_output_non_empty(self):
        """All generated replies should be non-empty."""
        for tone in ["cercano", "formal", "moderno"]:
            reply = generate_reply_by_tone(
                tone=tone,
                review_text="Test review",
                stars=4,
                business_name="Business",
                author_name="Author",
            )
            assert len(reply.strip()) > 0

    def test_output_contains_author_name(self):
        """Replies should include author name."""
        reply = generate_reply_by_tone(
            tone="cercano",
            review_text="Good",
            stars=5,
            business_name="Biz",
            author_name="JohnDoe",
        )
        assert "JohnDoe" in reply

    def test_output_contains_business_name(self):
        """Replies should include business name."""
        reply = generate_reply_by_tone(
            tone="formal",
            review_text="Good",
            stars=5,
            business_name="MyCompany Ltd",
            author_name="Client",
        )
        assert "MyCompany Ltd" in reply or "MyCompany" in reply

    def test_output_is_string(self):
        """Output should always be a string."""
        reply = generate_reply_by_tone(
            tone="moderno",
            review_text="Amazing",
            stars=5,
            business_name="Biz",
            author_name="User",
        )
        assert isinstance(reply, str)
