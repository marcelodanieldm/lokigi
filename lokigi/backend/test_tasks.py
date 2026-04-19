from backend.tasks.scraping import run_scraper
from backend.tasks.ai_insights import run_ai

def test_scraper_task():
    result = run_scraper.apply(args=["https://example.com"])
    assert result.successful()
    assert result.result["status"] == "done"

def test_ai_task():
    result = run_ai.apply(args=[{"foo": "bar"}])
    assert result.successful()
    assert result.result["insights"] == "ok"
