"""Unit tests for the sentiment analysis / concept extraction module.

These tests run without a database, Docker or external services.
Run with:  pytest tests/unit/test_sentiment_analysis.py -v
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from app.sentiment_analysis import analyze_monthly_sentiment, _extract_concepts


# ---------------------------------------------------------------------------
# _extract_concepts  – keyword matching
# ---------------------------------------------------------------------------

class TestExtractConcepts:
    def test_matches_spanish_speed_keyword(self):
        concepts = _extract_concepts("El servicio fue muy rápido y eficiente")
        assert "rapidez" in concepts

    def test_matches_english_price_keyword(self):
        concepts = _extract_concepts("The prices are way too expensive")
        assert "precio / costo" in concepts

    def test_matches_wait_time_spanish(self):
        concepts = _extract_concepts("La espera fue demasiado larga, tardaron mucho")
        assert "tiempo de espera" in concepts

    def test_matches_cleanliness(self):
        concepts = _extract_concepts("El lugar estaba muy sucio y sin higiene")
        assert "limpieza" in concepts

    def test_empty_text_returns_empty(self):
        assert _extract_concepts("") == []

    def test_none_safe_text_returns_empty(self):
        # _extract_concepts handles None via or-default in analyze pipeline;
        # direct call with empty string must not raise
        assert _extract_concepts("   ") == []

    def test_no_false_positive_on_unrelated_text(self):
        # A generic greeting should not match specific concepts
        concepts = _extract_concepts("Hola, todo bien, gracias.")
        assert "precio / costo" not in concepts
        assert "tiempo de espera" not in concepts

    def test_multiple_concepts_in_one_review(self):
        concepts = _extract_concepts(
            "La atención fue excelente y el lugar estaba muy limpio, además los precios son muy accesibles"
        )
        assert "atención al cliente" in concepts
        assert "limpieza" in concepts
        assert "precio / costo" in concepts


# ---------------------------------------------------------------------------
# analyze_monthly_sentiment – integration of full pipeline
# ---------------------------------------------------------------------------

SAMPLE_REVIEWS = [
    # Positive (5★) – mentions: rapidez, atención, ambiente
    {"rating": 5, "comment": "Muy rápido y el personal muy amable. El ambiente es precioso."},
    # Positive (4★) – mentions: atención, calidad del producto
    {"rating": 4, "comment": "Excelente atención y calidad del producto impecable."},
    # Positive (5★) – mentions: rapidez, precio
    {"rating": 5, "comment": "Servicio rápido y precios económicos, lo recomiendo."},
    # Positive (4★) – mentions: limpieza, ambiente
    {"rating": 4, "comment": "El lugar está muy limpio y tiene un ambiente muy agradable."},
    # Neutral (3★) – should be SKIPPED
    {"rating": 3, "comment": "Nada especial, servicio normal."},
    # Negative (2★) – mentions: espera, precio
    {"rating": 2, "comment": "La espera fue horrible y encima los precios son muy caros."},
    # Negative (1★) – mentions: espera, limpieza
    {"rating": 1, "comment": "Tardaron una eternidad y el baño estaba sucio."},
    # Negative (2★) – mentions: comunicación
    {"rating": 2, "comment": "Nadie contesta el teléfono y nunca responden."},
]


class TestAnalyzeMonthlySentiment:
    def setup_method(self):
        self.report = analyze_monthly_sentiment(
            SAMPLE_REVIEWS,
            year=2026,
            month=4,
            location_id="loc-test-001",
        )

    def test_basic_counts(self):
        assert self.report.positive_reviews == 4
        assert self.report.neutral_reviews == 1
        assert self.report.negative_reviews == 3
        assert self.report.total_reviews_analyzed == 8

    def test_top_n_limit(self):
        assert len(self.report.positive_concepts) <= 5
        assert len(self.report.negative_concepts) <= 5
        assert len(self.report.top_concepts) <= 5

    def test_positive_concepts_are_present(self):
        pos_labels = [h.concept for h in self.report.positive_concepts]
        # rapidez appears in 2 of 4 positive reviews → should be top
        assert "rapidez" in pos_labels

    def test_negative_concepts_are_present(self):
        neg_labels = [h.concept for h in self.report.negative_concepts]
        # espera appears in 2 negative reviews → should be in top 3
        assert "tiempo de espera" in neg_labels

    def test_counts_are_positive_integers(self):
        for hit in self.report.positive_concepts + self.report.negative_concepts:
            assert hit.count >= 1

    def test_pct_is_between_0_and_100(self):
        for hit in self.report.positive_concepts + self.report.negative_concepts:
            assert 0.0 <= hit.pct <= 100.0

    def test_to_dict_structure(self):
        d = self.report.to_dict()
        assert d["period"] == {"year": 2026, "month": 4}
        assert d["location_id"] == "loc-test-001"
        assert isinstance(d["positive_concepts"], list)
        assert isinstance(d["negative_concepts"], list)
        assert isinstance(d["top_concepts"], list)
        assert "sentiment_snapshot" in d
        assert "chart_data" in d

    def test_sentiment_snapshot_structure(self):
        snapshot = self.report.to_dict()["sentiment_snapshot"]
        assert snapshot["labels"] == ["Positivas", "Neutrales", "Negativas"]
        assert snapshot["counts"] == [4, 1, 3]
        assert len(snapshot["percentages"]) == 3

    def test_top_concepts_include_cross_sentiment_mentions(self):
        labels = [h["concept"] for h in self.report.to_dict()["top_concepts"]]
        assert "atención al cliente" in labels or "tiempo de espera" in labels

    def test_chart_data_structure(self):
        cd = self.report.to_dict()["chart_data"]
        assert "labels" in cd
        assert "positive" in cd
        assert "negative" in cd
        # All arrays must have the same length
        assert len(cd["labels"]) == len(cd["positive"]) == len(cd["negative"])

    def test_chart_data_no_negative_values_in_positive_slots(self):
        """A concept that is purely negative should have 0 in the positive array."""
        d = self.report.to_dict()
        cd = d["chart_data"]
        neg_only = [h["concept"] for h in d["negative_concepts"]
                    if h["concept"] not in [h2["concept"] for h2 in d["positive_concepts"]]]
        for label in neg_only:
            idx = cd["labels"].index(label)
            assert cd["positive"][idx] == 0

    def test_empty_reviews_returns_zero_counts(self):
        report = analyze_monthly_sentiment(
            [], year=2026, month=1, location_id="loc-empty"
        )
        assert report.total_reviews_analyzed == 0
        assert report.positive_concepts == []
        assert report.negative_concepts == []

    def test_only_neutral_reviews_returns_zero_counts(self):
        neutral = [{"rating": 3, "comment": "Nada del otro mundo"} for _ in range(5)]
        report = analyze_monthly_sentiment(
            neutral, year=2026, month=1, location_id="loc-neutral"
        )
        assert report.total_reviews_analyzed == 5
        assert report.neutral_reviews == 5

    def test_custom_top_n(self):
        report = analyze_monthly_sentiment(
            SAMPLE_REVIEWS,
            year=2026,
            month=4,
            location_id="loc-test-001",
            top_n=2,
        )
        assert len(report.positive_concepts) <= 2
        assert len(report.negative_concepts) <= 2

    def test_missing_comment_does_not_crash(self):
        reviews = [
            {"rating": 5, "comment": None},
            {"rating": 1, "comment": None},
        ]
        report = analyze_monthly_sentiment(
            reviews, year=2026, month=1, location_id="loc-null"
        )
        assert report.positive_reviews == 1
        assert report.negative_reviews == 1
        assert report.positive_concepts == []
        assert report.negative_concepts == []
