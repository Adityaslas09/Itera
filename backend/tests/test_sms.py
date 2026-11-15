import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Itera"

def test_prometheus_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"itera_ai_requests_total" in response.content

def test_twilio_webhook_endpoint():
    form_data = {
        "From": "+15553334444",
        "Body": "I love warm beaches, local seafood, budget $1200 max"
    }
    response = client.post("/api/v1/sms/webhook", data=form_data)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert b"<Response><Message>" in response.content

def test_sms_simulate_endpoint():
    payload = {
        "trip_id": "demo-trip-1",
        "participant_phone": "+15553334444",
        "message_body": "Looking for coastal hiking and authentic seafood under $1400"
    }
    response = client.post("/api/v1/sms/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["parsed_preferences"] is not None
