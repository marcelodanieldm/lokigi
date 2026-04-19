from fastapi.testclient import TestClient
from backend.main import app

def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_start_scraping():
    client = TestClient(app)
    resp = client.post("/start-scraping", json={"url": "https://example.com"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "scraping started"

def test_process_insights():
    client = TestClient(app)
    resp = client.post("/process-insights", json={"data": {"foo": "bar"}})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ai processing started"
