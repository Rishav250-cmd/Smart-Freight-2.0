"""Tests for Google Routes API lookups, OSRM fallback, and route caching."""

import asyncio
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import respx

from app.config import Settings
from app.schemas import Place, RouteInfo
from app.services import routes

ORIGIN = Place(name="Delhi", lat=28.6139, lng=77.209)
DESTINATION = Place(name="Chennai", lat=13.0827, lng=80.2707)
DEPARTURE_TIME = datetime(2026, 12, 2, 8, 30, tzinfo=timezone.utc)
OSRM_URL = (
    f"{routes.OSRM_ROUTE_URL}/{ORIGIN.lng},{ORIGIN.lat};"
    f"{DESTINATION.lng},{DESTINATION.lat}?overview=full&geometries=polyline"
)
GOOGLE_RESPONSE = {
    "routes": [
        {
            "distanceMeters": 2180400,
            "duration": "9000s",
            "staticDuration": "8400s",
            "polyline": {"encodedPolyline": "google_encoded_polyline"},
        }
    ]
}
OSRM_RESPONSE = {
    "code": "Ok",
    "routes": [
        {
            "distance": 2180400,
            "duration": 9600,
            "geometry": "osrm_encoded_polyline",
        }
    ],
}


def _run_route(departure_time: datetime = DEPARTURE_TIME) -> RouteInfo:
    async def run() -> RouteInfo:
        try:
            return await routes.get_route(ORIGIN, DESTINATION, departure_time)
        finally:
            await routes.close_route_client()

    return asyncio.run(run())


def _configure_google_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        routes,
        "get_settings",
        lambda: Settings(google_maps_server_key="test-server-key"),
    )


def setup_function() -> None:
    routes.clear_route_cache()


def test_google_success_maps_route_fields_and_request(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_google_key(monkeypatch)
    with respx.mock(assert_all_called=False) as mock:
        google = mock.post(routes.GOOGLE_ROUTES_URL).mock(
            return_value=httpx.Response(200, json=GOOGLE_RESPONSE)
        )

        route = _run_route()

    assert route == RouteInfo(
        distance_km=2180.4,
        normal_min=140.0,
        traffic_min=150.0,
        traffic_ratio=150 / 140,
        polyline="google_encoded_polyline",
        source="google",
    )
    request = google.calls[0].request
    assert request.headers["X-Goog-Api-Key"] == "test-server-key"
    assert request.headers["X-Goog-FieldMask"] == routes.GOOGLE_FIELD_MASK
    body = request.read()
    assert b'"travelMode":"DRIVE"' in body
    assert b'"routingPreference":"TRAFFIC_AWARE"' in body
    assert b'"latitude":28.6139' in body


def test_past_departure_time_is_replaced_with_now(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_google_key(monkeypatch)
    with respx.mock(assert_all_called=False) as mock:
        google = mock.post(routes.GOOGLE_ROUTES_URL).mock(
            return_value=httpx.Response(200, json=GOOGLE_RESPONSE)
        )

        _run_route(datetime(2020, 1, 1, tzinfo=timezone.utc))

    body = google.calls[0].request.read()
    departure_text = json.loads(body)["departureTime"]
    departure_time = datetime.fromisoformat(departure_text.replace("Z", "+00:00"))
    assert datetime.now(timezone.utc) - timedelta(seconds=5) <= departure_time
    assert departure_time <= datetime.now(timezone.utc) + timedelta(seconds=1)


def test_google_403_falls_back_to_osrm(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_google_key(monkeypatch)
    with respx.mock() as mock:
        mock.post(routes.GOOGLE_ROUTES_URL).mock(return_value=httpx.Response(403))
        osrm = mock.get(OSRM_URL).mock(return_value=httpx.Response(200, json=OSRM_RESPONSE))

        route = _run_route()

    assert osrm.called
    assert route.source == "osrm"
    assert route.distance_km == 2180.4
    assert route.normal_min == 160.0
    assert route.traffic_min == route.normal_min
    assert route.traffic_ratio == 1.0
    assert route.polyline == "osrm_encoded_polyline"


def test_google_timeout_falls_back_to_osrm(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_google_key(monkeypatch)
    with respx.mock() as mock:
        mock.post(routes.GOOGLE_ROUTES_URL).mock(
            side_effect=httpx.ReadTimeout("Google timed out")
        )
        osrm = mock.get(OSRM_URL).mock(return_value=httpx.Response(200, json=OSRM_RESPONSE))

        route = _run_route()

    assert osrm.called
    assert route.source == "osrm"
    assert route.traffic_min == route.normal_min


def test_cache_hit_avoids_second_google_and_osrm_call(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_google_key(monkeypatch)
    with respx.mock(assert_all_called=False) as mock:
        google = mock.post(routes.GOOGLE_ROUTES_URL).mock(
            return_value=httpx.Response(200, json=GOOGLE_RESPONSE)
        )
        osrm = mock.get(OSRM_URL).mock(return_value=httpx.Response(200, json=OSRM_RESPONSE))

        first = _run_route()
        second = _run_route()

    assert google.call_count == 1
    assert osrm.call_count == 0
    assert first == second
