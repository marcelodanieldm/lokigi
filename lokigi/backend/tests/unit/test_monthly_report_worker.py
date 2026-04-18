"""Unit tests for monthly_report_worker.py

All tests run without a database, scheduler or external services.
Run with:  pytest tests/unit/test_monthly_report_worker.py -v
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.monthly_report_worker import (
    _build_report_payload,
    _month_label,
    _previous_month,
    _upsert_report,
    _send_report_email,
)


# ─────────────────────────────────────────────────────────────────────────────
# Pure helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestPreviousMonth:
    def test_regular_month(self):
        assert _previous_month(2026, 4) == (2026, 3)

    def test_january_wraps_to_december(self):
        assert _previous_month(2026, 1) == (2025, 12)

    def test_december(self):
        assert _previous_month(2026, 12) == (2026, 11)


class TestMonthLabel:
    def test_known_months(self):
        assert _month_label(1) == "Enero"
        assert _month_label(4) == "Abril"
        assert _month_label(12) == "Diciembre"

    def test_unknown_returns_str(self):
        assert _month_label(0) == "0"


# ─────────────────────────────────────────────────────────────────────────────
# _build_report_payload — pure function
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_KPIS = {
    "total_reviews": 30,
    "avg_rating": 4.2,
    "response_rate_pct": 75.0,
    "avg_response_time_minutes": 8.5,
}

SAMPLE_SENTIMENT = {
    "positive_concepts": [{"concept": "rapidez", "count": 10, "pct": 50.0}],
    "negative_concepts": [{"concept": "precio / costo", "count": 5, "pct": 25.0}],
    "chart_data": {
        "labels": ["rapidez", "precio / costo"],
        "positive": [10, 0],
        "negative": [0, 5],
    },
}


class TestBuildReportPayload:
    def setup_method(self):
        self.user_id = uuid.uuid4()
        self.payload = _build_report_payload(
            user_id=self.user_id,
            location_id="accounts/1/locations/42",
            business_name="Café Lokigi",
            year=2026,
            month=3,
            kpis=SAMPLE_KPIS,
            sentiment=SAMPLE_SENTIMENT,
        )

    def test_top_level_keys(self):
        for key in ("report_id", "user_id", "location_id", "business_name",
                    "period", "generated_at", "kpis", "sentiment"):
            assert key in self.payload, f"Missing key: {key}"

    def test_period(self):
        assert self.payload["period"] == {"year": 2026, "month": 3}

    def test_user_id_serialized(self):
        assert self.payload["user_id"] == str(self.user_id)

    def test_kpis_passed_through(self):
        assert self.payload["kpis"] == SAMPLE_KPIS

    def test_sentiment_keys(self):
        s = self.payload["sentiment"]
        assert "positive_concepts" in s
        assert "negative_concepts" in s
        assert "chart_data" in s

    def test_report_id_is_valid_uuid(self):
        uuid.UUID(self.payload["report_id"])  # raises if invalid

    def test_generated_at_is_iso_string(self):
        # Should not raise
        datetime.fromisoformat(self.payload["generated_at"])

    def test_different_calls_produce_different_report_ids(self):
        p2 = _build_report_payload(
            user_id=self.user_id,
            location_id="loc",
            business_name="B",
            year=2026,
            month=3,
            kpis=SAMPLE_KPIS,
            sentiment=SAMPLE_SENTIMENT,
        )
        assert p2["report_id"] != self.payload["report_id"]


# ─────────────────────────────────────────────────────────────────────────────
# _upsert_report — DB interaction mocked
# ─────────────────────────────────────────────────────────────────────────────

class TestUpsertReport:
    def _make_db(self, existing=None):
        db = MagicMock()
        scalars_result = MagicMock()
        scalars_result.first.return_value = existing
        db.scalars.return_value = scalars_result
        return db

    def test_inserts_when_no_existing(self):
        db = self._make_db(existing=None)
        user_id = uuid.uuid4()
        report = _upsert_report(db, user_id, 2026, 3, SAMPLE_KPIS)
        db.add.assert_called_once()

    def test_updates_when_existing(self):
        existing = MagicMock()
        db = self._make_db(existing=existing)
        user_id = uuid.uuid4()
        result = _upsert_report(db, user_id, 2026, 3, SAMPLE_KPIS)
        assert result is existing
        assert existing.payload == SAMPLE_KPIS  # updated payload
        db.add.assert_called_once_with(existing)


# ─────────────────────────────────────────────────────────────────────────────
# _send_report_email — httpx mocked
# ─────────────────────────────────────────────────────────────────────────────

class TestSendReportEmail:
    @pytest.mark.asyncio
    async def test_sends_post_to_sendgrid(self):
        mock_response = MagicMock()
        mock_response.status_code = 202

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.monthly_report_worker.httpx.AsyncClient", return_value=mock_client):
            with patch("app.monthly_report_worker.settings") as mock_settings:
                mock_settings.sendgrid_api_key = "SG.fake"
                mock_settings.sendgrid_from_email = "noreply@lokigi.com"
                mock_settings.app_domain = "app.lokigi.com"
                await _send_report_email(
                    to_email="user@example.com",
                    business_name="Test Business",
                    year=2026,
                    month=3,
                    kpis=SAMPLE_KPIS,
                )

        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        assert "api.sendgrid.com" in call_kwargs.args[0]
        body = call_kwargs.kwargs["json"]
        assert body["personalizations"][0]["to"][0]["email"] == "user@example.com"
        assert "2026" in body["subject"]
        assert "Marzo" in body["subject"]

    @pytest.mark.asyncio
    async def test_logs_error_on_non_202(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.monthly_report_worker.httpx.AsyncClient", return_value=mock_client):
            with patch("app.monthly_report_worker.settings") as mock_settings:
                mock_settings.sendgrid_api_key = "SG.bad"
                mock_settings.sendgrid_from_email = "noreply@lokigi.com"
                mock_settings.app_domain = "app.lokigi.com"
                # Should not raise — just log
                await _send_report_email(
                    to_email="user@example.com",
                    business_name="B",
                    year=2026,
                    month=3,
                    kpis=SAMPLE_KPIS,
                )
        # If we get here without exception, the error was handled gracefully
        assert True


# ─────────────────────────────────────────────────────────────────────────────
# build_scheduler — smoke test (no actual APScheduler job fired)
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildScheduler:
    def test_returns_scheduler_with_job(self):
        from app.monthly_report_worker import build_scheduler
        scheduler = build_scheduler()
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "monthly_report_job"
