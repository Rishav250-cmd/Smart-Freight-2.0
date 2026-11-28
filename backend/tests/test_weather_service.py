"""Tests for route weather selection, fallback, and caching."""

import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import polyline
import pytest
import respx

from app.schemas import WeatherPoint
from app.services import weather

OPEN_METEO_URL = weather.OPEN_METEO_URL
ROUTE_COORDINATES = [(10.0, 70.0), (20.0, 75.0), (30.0, 80.0)]
ROUTE_POLYLINE = polyline.encode(ROUTE_COORDINATES)


def _forecast(
    times: list[str],
    precipitation: list[float],
    wind_speed: list[float],
    weather_code: list[int],
) -> dict[str, object]:
    return {
        "hourly": {
            "time": times,
            "precipitation": precipitation,
            "wind_speed_10m": wind_speed,
            "weather_code": weather_code,
        }
    }


def _run_weather(
    departure_time: datetime,
    traffic_min: float,
    route_polyline: str = ROUTE_POLYLINE,
) -> list[WeatherPoint]:
    async def run() -> list[WeatherPoint]:
        try:
            return await weather.get_route_weather(
                route_polyline, departure_time, traffic_min
            )
        finally:
            await weather.close_weather_client()

    return asyncio.run(run())


def setup_function() -> None:
    weather.clear_weather_cache()


def test_normal_case_uses_nearest_hours_concurrently_and_caches() -> None:
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    hours = [start + timedelta(hours=index) for index in range(5)]
    hour_strings = [value.strftime("%Y-%m-%dT%H:%M") for value in hours]
    departure_time = start + timedelta(hours=1)
    response_data = _forecast(
        hour_strings,
        [0.0, 4.0, 9.0, 2.0, 0.0],
        [0.0, 25.0, 40.0, 50.0, 0.0],
        [0, 61, 95, 0, 0],
    )

    with respx.mock() as mock:
        forecast_route = mock.get(OPEN_METEO_URL).mock(
            return_value=httpx.Response(200, json=response_data)
        )
        points = _run_weather(departure_time, traffic_min=120)
        cached_points = _run_weather(departure_time, traffic_min=120)

    assert len(points) == 3
    assert [point.time for point in points] == hours[1:4]
    assert [point.severity for point in points] == pytest.approx([0.425, 0.85, 0.35])
    assert points[0].summary == "Rain 4.0 mm, wind 25 km/h"
    assert points == cached_points
    assert forecast_route.call_count == 3
    params = forecast_route.calls[0].request.url.params
    assert params["hourly"] == "precipitation,wind_speed_10m,weather_code"
    assert params["timezone"] == "UTC"
    assert params["forecast_days"] == "7"
    assert params["wind_speed_unit"] == "kmh"


def test_one_point_failure_skips_only_that_point() -> None:
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    response_data = _forecast(
        [(start + timedelta(hours=index)).strftime("%Y-%m-%dT%H:%M") for index in range(4)],
        [1.0, 2.0, 3.0, 4.0],
        [10.0, 20.0, 30.0, 40.0],
        [0, 61, 95, 0],
    )

    def response_for_point(request: httpx.Request) -> httpx.Response:
        if float(request.url.params["latitude"]) == 20.0:
            return httpx.Response(503)
        return httpx.Response(200, json=response_data)

    with respx.mock() as mock:
        forecast_route = mock.get(OPEN_METEO_URL).mock(side_effect=response_for_point)
        points = _run_weather(start, traffic_min=120)

    assert forecast_route.call_count == 3
    assert len(points) == 2
    assert [point.lat for point in points] == [10.0, 30.0]


def test_all_point_failures_return_empty_list() -> None:
    with respx.mock() as mock:
        forecast_route = mock.get(OPEN_METEO_URL).mock(
            side_effect=httpx.ConnectError("Open-Meteo unavailable")
        )
        points = _run_weather(datetime.now(timezone.utc), traffic_min=60)

    assert forecast_route.call_count == 3
    assert points == []


def test_time_after_forecast_range_uses_last_available_hour() -> None:
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    last_hour = start + timedelta(hours=2)
    response_data = _forecast(
        [
            start.strftime("%Y-%m-%dT%H:%M"),
            (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
            last_hour.strftime("%Y-%m-%dT%H:%M"),
        ],
        [0.0, 1.0, 8.0],
        [1.0, 2.0, 3.0],
        [0, 61, 95],
    )
    departure_time = last_hour + timedelta(days=8)

    with respx.mock() as mock:
        mock.get(OPEN_METEO_URL).mock(return_value=httpx.Response(200, json=response_data))
        points = _run_weather(departure_time, traffic_min=60)

    assert len(points) == 3
    assert all(point.time == last_hour for point in points)
    assert all(point.summary == "Rain 8.0 mm, wind 3 km/h" for point in points)
