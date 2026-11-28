"""API smoke tests and validation of every checked-in JSON contract."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import (
    AssessRequest,
    AssessResponse,
    CalibrationAnalytics,
    HealthResponse,
    HistoryResponse,
    ImpactAnalytics,
    LanesAnalytics,
    RecommendResponse,
    ShapAnalytics,
    TrackResponse,
    ThresholdAnalytics,
    WhatIfRequest,
    WhatIfResponse,
)

client = TestClient(app)
CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"

CONTRACT_MODELS = {
    "assess.request.json": AssessRequest,
    "assess.response.json": AssessResponse,
    "whatif.request.json": WhatIfRequest,
    "whatif.response.json": WhatIfResponse,
    "recommend.response.json": RecommendResponse,
    "history.response.json": HistoryResponse,
    "track.response.json": TrackResponse,
    "health.response.json": HealthResponse,
    "analytics.threshold.json": ThresholdAnalytics,
    "analytics.impact.json": ImpactAnalytics,
    "analytics.lanes.json": LanesAnalytics,
    "analytics.shap.json": ShapAnalytics,
    "analytics.calibration.json": CalibrationAnalytics,
}


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


@pytest.mark.parametrize(("filename", "model"), CONTRACT_MODELS.items())
def test_contract_example_matches_schema(filename: str, model: type) -> None:
    contract_path = CONTRACTS_DIR / filename
    assert contract_path.is_file()
    payload = json.loads(contract_path.read_text(encoding="utf-8"))

    model.model_validate(payload)


def test_contract_directory_contains_only_mapped_json_examples() -> None:
    contract_files = {path.name for path in CONTRACTS_DIR.glob("*.json")}

    assert contract_files == set(CONTRACT_MODELS)
