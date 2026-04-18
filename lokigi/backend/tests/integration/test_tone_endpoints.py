"""Integration tests for tone selection API endpoints.

Tests:
- POST /api/tone-preview - Preview generation
- POST /api/tone/set - Save tone preference  
- GET /api/tone/current - Retrieve current tone
- GET /starter/tone-selector - HTML page rendering
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import GoogleConnection, User
from app.config import settings


client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_connection(db: Session, test_user: User):
    """Create a test Google connection."""
    from cryptography.fernet import Fernet
    
    cipher = Fernet(settings.encryption_key.encode())
    token = cipher.encrypt(b"test_access_token").decode()
    refresh = cipher.encrypt(b"test_refresh_token").decode()
    
    from datetime import datetime, timedelta
    conn = GoogleConnection(
        user_id=test_user.id,
        google_account_name="test@gmail.com",
        business_name="Test Business",
        location_id="12345",
        encrypted_access_token=token,
        encrypted_refresh_token=refresh,
        token_expiry=datetime.utcnow() + timedelta(days=1),
        preferred_tone="cercano",
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


class TestTonePreviewEndpoint:
    """Tests for POST /api/tone-preview."""

    def test_preview_cercano(self):
        """Generate preview with cercano tone."""
        res = client.post(
            "/api/tone-preview",
            json={
                "tone": "cercano",
                "review_text": "¡Excelente servicio!",
                "stars": 5,
                "business_name": "Mi Negocio",
                "author_name": "Juan",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "preview" in data
        assert "tone" in data
        assert data["tone"] == "cercano"
        assert "Juan" in data["preview"]
        assert len(data["preview"]) > 20

    def test_preview_formal(self):
        """Generate preview with formal tone."""
        res = client.post(
            "/api/tone-preview",
            json={
                "tone": "formal",
                "review_text": "Good service",
                "stars": 4,
                "business_name": "Company",
                "author_name": "Client",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["tone"] == "formal"
        assert "Client" in data["preview"]

    def test_preview_moderno(self):
        """Generate preview with moderno tone."""
        res = client.post(
            "/api/tone-preview",
            json={
                "tone": "moderno",
                "review_text": "Amazing!",
                "stars": 5,
                "business_name": "Startup",
                "author_name": "User",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["tone"] == "moderno"
        assert "User" in data["preview"]

    def test_preview_case_insensitive_tone(self):
        """Tone parameter should be case-insensitive."""
        res1 = client.post(
            "/api/tone-preview",
            json={
                "tone": "FORMAL",
                "review_text": "Test",
                "stars": 5,
                "business_name": "Biz",
                "author_name": "Author",
            },
        )
        res2 = client.post(
            "/api/tone-preview",
            json={
                "tone": "formal",
                "review_text": "Test",
                "stars": 5,
                "business_name": "Biz",
                "author_name": "Author",
            },
        )
        assert res1.status_code == 200
        assert res2.status_code == 200
        assert res1.json()["preview"] == res2.json()["preview"]

    def test_preview_with_special_characters(self):
        """Should handle special characters in review text."""
        res = client.post(
            "/api/tone-preview",
            json={
                "tone": "cercano",
                "review_text": "¡Excelente! ★★★★★ 👍",
                "stars": 5,
                "business_name": "Café & Bar",
                "author_name": "José María",
            },
        )
        assert res.status_code == 200
        assert "José María" in res.json()["preview"]


class TestToneSetEndpoint:
    """Tests for POST /api/tone/set."""

    def test_set_tone_cercano(self, test_user: User, test_connection: GoogleConnection, db: Session):
        """Save cercano tone preference."""
        res = client.post(
            "/api/tone/set",
            json={"user_id": str(test_user.id), "tone": "cercano"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "saved"
        assert res.json()["preferred_tone"] == "cercano"
        
        # Verify in DB
        db.refresh(test_connection)
        assert test_connection.preferred_tone == "cercano"

    def test_set_tone_formal(self, test_user: User, db: Session):
        """Save formal tone preference."""
        res = client.post(
            "/api/tone/set",
            json={"user_id": str(test_user.id), "tone": "formal"},
        )
        assert res.status_code == 200
        assert res.json()["preferred_tone"] == "formal"

    def test_set_tone_moderno(self, test_user: User, db: Session):
        """Save moderno tone preference."""
        res = client.post(
            "/api/tone/set",
            json={"user_id": str(test_user.id), "tone": "moderno"},
        )
        assert res.status_code == 200
        assert res.json()["preferred_tone"] == "moderno"

    def test_set_tone_invalid(self, test_user: User):
        """Invalid tone should return 400 error."""
        res = client.post(
            "/api/tone/set",
            json={"user_id": str(test_user.id), "tone": "invalid_tone"},
        )
        assert res.status_code == 400
        assert "Invalid tone" in res.json()["detail"]

    def test_set_tone_nonexistent_user(self):
        """Nonexistent user should return 404."""
        fake_user_id = str(uuid4())
        res = client.post(
            "/api/tone/set",
            json={"user_id": fake_user_id, "tone": "cercano"},
        )
        assert res.status_code == 404

    def test_set_tone_case_insensitive(self, test_user: User):
        """Tone should be saved in lowercase."""
        res = client.post(
            "/api/tone/set",
            json={"user_id": str(test_user.id), "tone": "FORMAL"},
        )
        assert res.status_code == 200
        assert res.json()["preferred_tone"] == "formal"


class TestToneCurrentEndpoint:
    """Tests for GET /api/tone/current."""

    def test_get_current_tone(self, test_user: User, test_connection: GoogleConnection):
        """Retrieve current tone preference."""
        res = client.get(f"/api/tone/current?user_id={test_user.id}")
        assert res.status_code == 200
        assert res.json()["tone"] == "cercano"

    def test_get_current_tone_after_change(self, test_user: User, db: Session):
        """Tone should reflect recent changes."""
        # Set to formal
        client.post(
            "/api/tone/set",
            json={"user_id": str(test_user.id), "tone": "formal"},
        )
        
        # Get current
        res = client.get(f"/api/tone/current?user_id={test_user.id}")
        assert res.status_code == 200
        assert res.json()["tone"] == "formal"

    def test_get_current_nonexistent_user(self):
        """Nonexistent user should return 404."""
        fake_user_id = uuid4()
        res = client.get(f"/api/tone/current?user_id={fake_user_id}")
        assert res.status_code == 404


class TestStarterActivationEndpoint:
    """Tests for POST /api/starter/activate."""

    def test_activate_starter_persists_flags(self, test_user: User, test_connection: GoogleConnection, db: Session):
        res = client.post(
            "/api/starter/activate",
            json={
                "user_id": str(test_user.id),
                "tone": "moderno",
                "manual_approval": True,
                "whatsapp_negative_alerts": True,
            },
        )

        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "activated"
        assert body["preferred_tone"] == "moderno"
        assert body["manual_approval_enabled"] is True
        assert body["negative_review_whatsapp_enabled"] is True

        db.refresh(test_connection)
        assert test_connection.preferred_tone == "moderno"
        assert test_connection.manual_approval_enabled is True
        assert test_connection.negative_review_whatsapp_enabled is True

    def test_activate_starter_invalid_tone(self, test_user: User):
        res = client.post(
            "/api/starter/activate",
            json={
                "user_id": str(test_user.id),
                "tone": "serio-premium",
                "manual_approval": True,
                "whatsapp_negative_alerts": False,
            },
        )
        assert res.status_code == 400
        assert "Invalid tone" in res.json()["detail"]


class TestToneSelectorPage:
    """Tests for GET /starter/tone-selector."""

    def test_tone_selector_page_renders(self, test_user: User, test_connection: GoogleConnection):
        """Tone selector page should render successfully."""
        res = client.get(f"/starter/tone-selector?user_id={test_user.id}")
        assert res.status_code == 200
        assert res.headers["content-type"] == "text/html; charset=utf-8"
        
        html = res.text
        # Should contain the three tone cards
        assert "Cercano" in html
        assert "Formal" in html
        assert "Moderno" in html
        
        # Should contain interactive elements
        assert "tone-card" in html
        assert "data-tone" in html
        assert "selectTone" in html

    def test_tone_selector_nonexistent_user(self):
        """Nonexistent user should return 404."""
        fake_user_id = uuid4()
        res = client.get(f"/starter/tone-selector?user_id={fake_user_id}")
        assert res.status_code == 404

    def test_tone_selector_contains_business_name(self, test_user: User, test_connection: GoogleConnection):
        """Page should show business name."""
        res = client.get(f"/starter/tone-selector?user_id={test_user.id}")
        assert res.status_code == 200
        assert "Test Business" in res.text

    def test_tone_selector_contains_preview_section(self, test_user: User, test_connection: GoogleConnection):
        """Page should have preview section."""
        res = client.get(f"/starter/tone-selector?user_id={test_user.id}")
        assert res.status_code == 200
        html = res.text
        assert "preview-content" in html
        assert "Adelanto" in html or "preview" in html.lower()

    def test_tone_selector_has_form_elements(self, test_user: User, test_connection: GoogleConnection):
        """Page should have confirm button and proper form."""
        res = client.get(f"/starter/tone-selector?user_id={test_user.id}")
        assert res.status_code == 200
        html = res.text
        assert "confirm-btn" in html or "Confirmar" in html
        assert "tone" in html


class TestToneIntegrationFlow:
    """End-to-end tests for tone selection flow."""

    def test_complete_tone_flow(self, test_user: User):
        """Complete flow: view page -> select tone -> confirm."""
        # 1. View tone selector page
        res1 = client.get(f"/starter/tone-selector?user_id={test_user.id}")
        assert res1.status_code == 200
        
        # 2. Preview a tone
        res2 = client.post(
            "/api/tone-preview",
            json={
                "tone": "formal",
                "review_text": "Good service",
                "stars": 5,
                "business_name": "Business",
                "author_name": "Client",
            },
        )
        assert res2.status_code == 200
        preview = res2.json()["preview"]
        assert len(preview) > 0
        
        # 3. Set tone preference
        res3 = client.post(
            "/api/tone/set",
            json={"user_id": str(test_user.id), "tone": "formal"},
        )
        assert res3.status_code == 200
        
        # 4. Verify tone was saved
        res4 = client.get(f"/api/tone/current?user_id={test_user.id}")
        assert res4.status_code == 200
        assert res4.json()["tone"] == "formal"

    def test_tone_switch_flow(self, test_user: User):
        """User should be able to switch between tones."""
        # Set to formal
        client.post(
            "/api/tone/set",
            json={"user_id": str(test_user.id), "tone": "formal"},
        )
        
        # Get preview for moderno
        res = client.post(
            "/api/tone-preview",
            json={
                "tone": "moderno",
                "review_text": "Amazing",
                "stars": 5,
                "business_name": "Biz",
                "author_name": "User",
            },
        )
        assert res.status_code == 200
        
        # Switch to moderno
        client.post(
            "/api/tone/set",
            json={"user_id": str(test_user.id), "tone": "moderno"},
        )
        
        # Verify current is moderno
        res = client.get(f"/api/tone/current?user_id={test_user.id}")
        assert res.json()["tone"] == "moderno"
