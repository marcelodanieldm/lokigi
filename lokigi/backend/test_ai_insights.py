import pytest
from backend.tasks.ai_insights import run_ai

def test_ai_sentiment_extraction():
    review = "El servicio fue excelente y la comida deliciosa, pero el local estaba sucio."
    result = run_ai({"review_text": review})
    assert isinstance(result, dict)
    assert "sentiment" in result
    assert "entities" in result
    assert "competitive_gaps" in result
    assert isinstance(result["entities"], list)
    assert isinstance(result["competitive_gaps"], list)
    assert -1 <= result["sentiment"] <= 1
