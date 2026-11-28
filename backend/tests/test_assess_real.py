"""Tests for real-mode POST /assess orchestration."""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.routers import assess
from app.schemas import AssessResponse, RouteInfo, WeatherPoint

ASSESS_REQUEST = json.loads(
    (Path(__file__).resolve().parents[2] / "contracts" / "assess.request.json").read_text()
)
GOOGLE_ROUTE = RouteInfo(
    distance_km=2180.4,
    normal_min=1900.0,
    traffic_min=2375.0,
    traffic_ratio=1.25,
    polyline="encoded-route-polyline",
    source="google",
)
OSRM_ROUTE = RouteInfo(
    distance_km=2180.4,
    normal_min=2375.0,
    traffic_min=2375.0,
    traffic_ratio=1.0,
    polyline="encoded-route-polyline",
    source="osrm",
)
WEATHER_POINTS = [
    WeatherPoint(
        lat=21.1458,
        lng=79.0882,
        time=datetime(2026, 12, 4, 12, tzinfo=timezone.utc),
        severity=0.75,
        summary="Rain 8.0 mm, wind 35 km/h",
    )
]


def _set_real_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assess, "get_settings", lambda: Settings(use_mock=False))


def test_real_assess_normal_case(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_real_mode(monkeypatch)
    route_service = AsyncMock(return_value=GOOGLE_ROUTE)
    weather_service = AsyncMock(return_value=WEATHER_POINTS)
    monkeypatch.setattr(assess, "get_route", route_service)
    monkeypatch.setattr(assess, "get_route_weather", weather_service)

    with TestClient(main.app) as client:
        response = client.post("/assess", json=ASSESS_REQUEST)

    assert response.status_code == 200
    body = AssessResponse.model_validate(response.json())
    assert body.breakdown.weather == 11.25
    assert body.breakdown.traffic == 5.0
    assert body.breakdown.news == 0.0
    assert body.delay_pct == 42.0
    assert body.status == "caution"
    assert body.expected_delay_hours is None
    assert body.shap_top5 == []
    assert body.signals_available == {
        "route_traffic": True,
        "weather": True,
        "news": False,
    }
    route_service.assert_awaited_once()
    weather_service.assert_awaited_once_with(
        GOOGLE_ROUTE.polyline,
        datetime.fromisoformat(ASSESS_REQUEST["departure_time"].replace("Z", "+00:00")),
        GOOGLE_ROUTE.traffic_min,
    )


def test_osrm_fallback_marks_traffic_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_real_mode(monkeypatch)
    monkeypatch.setattr(assess, "get_route", AsyncMock(return_value=OSRM_ROUTE))
    monkeypatch.setattr(assess, "get_route_weather", AsyncMock(return_value=WEATHER_POINTS))

    with TestClient(main.app) as client:
        response = client.post("/assess", json=ASSESS_REQUEST)

    body = AssessResponse.model_validate(response.json())
    assert body.route.source == "osrm"
    assert body.signals_available["route_traffic"] is False
    assert body.signals_available["weather"] is True


def test_weather_failure_returns_assessment_without_weather_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_real_mode(monkeypatch)
    monkeypatch.setattr(assess, "get_route", AsyncMock(return_value=GOOGLE_ROUTE))
    monkeypatch.setattr(
        assess,
        "get_route_weather",
        AsyncMock(side_effect=RuntimeError("weather provider unavailable")),
    )

    with TestClient(main.app) as client:
        response = client.post("/assess", json=ASSESS_REQUEST)

    assert response.status_code == 200
    body = AssessResponse.model_validate(response.json())
    assert body.weather_points == []
    assert body.breakdown.weather == 0.0
    assert body.signals_available["weather"] is False


def test_real_assess_response_validates_against_assess_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_real_mode(monkeypatch)
    monkeypatch.setattr(assess, "get_route", AsyncMock(return_value=GOOGLE_ROUTE))
    monkeypatch.setattr(assess, "get_route_weather", AsyncMock(return_value=[]))

    with TestClient(main.app) as client:
        response = client.post("/assess", json=ASSESS_REQUEST)

    assert response.status_code == 200
    AssessResponse.model_validate(response.json())
