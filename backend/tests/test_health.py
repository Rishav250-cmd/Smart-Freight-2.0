"""Health endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_document_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "SmartFreight API"


def test_assess_rejects_zero_day_intercity_shipment() -> None:
    response = client.post(
        "/assess",
        json={
            "origin": {"name": "Delhi", "lat": 28.6139, "lng": 77.209},
            "destination": {"name": "Mumbai", "lat": 19.076, "lng": 72.8777},
            "departure_time": "2026-11-28T09:00:00Z",
            "shipping_mode": "Standard Class",
            "scheduled_days": 0,
            "quantity": 1,
            "order_value": 100.0,
            "department": "Apparel",
        },
    )

    assert response.status_code == 422
    assert "scheduled_days must be at least 1" in response.text
