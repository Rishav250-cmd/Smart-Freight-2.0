"""Route weather lookup using Open-Meteo hourly forecasts."""

import asyncio
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import httpx
import polyline
from cachetools import TTLCache

from app.config import get_settings
from app.schemas import WeatherPoint

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_TIMEOUT_SECONDS = 10.0
CACHE_MAXSIZE = 2048

# Placeholder weights; replace these with values from the ML teammate's context_config.json.
SEVERITY_WEIGHTS = {
    "precipitation": 0.5,
    "wind": 0.3,
    "weather_code": 0.2,
}

_weather_cache: TTLCache[tuple[float, float, str], WeatherPoint] = TTLCache(
    maxsize=CACHE_MAXSIZE,
    ttl=get_settings().cache_ttl_seconds,
)


@lru_cache(maxsize=1)
def _get_http_client() -> httpx.AsyncClient:
    """Return a shared client for concurrent Open-Meteo requests."""
    return httpx.AsyncClient(timeout=httpx.Timeout(WEATHER_TIMEOUT_SECONDS))


async def close_weather_client() -> None:
    """Close and clear the shared client during application shutdown."""
    if _get_http_client.cache_info().currsize:
        await _get_http_client().aclose()
        _get_http_client.cache_clear()


def clear_weather_cache() -> None:
    """Clear cached weather points, primarily for tests and explicit resets."""
    _weather_cache.clear()


async def get_route_weather(
    polyline_str: str,
    departure_time: datetime,
    traffic_min: float,
) -> list[WeatherPoint]:
    """Fetch hourly weather at the route's first, middle, and last points."""
    try:
        decoded_points = polyline.decode(polyline_str)
    except (TypeError, ValueError):
        return []
    if not decoded_points:
        return []

    point_indexes = (0, len(decoded_points) // 2, len(decoded_points) - 1)
    fractions = (0.0, 0.5, 1.0)
    departure = _as_utc(departure_time)
    point_requests = [
        _get_weather_point(
            decoded_points[index][0],
            decoded_points[index][1],
            departure + timedelta(minutes=traffic_min * fraction),
        )
        for index, fraction in zip(point_indexes, fractions, strict=True)
    ]
    results = await asyncio.gather(*point_requests, return_exceptions=True)
    return [result for result in results if isinstance(result, WeatherPoint)]


async def _get_weather_point(
    latitude: float,
    longitude: float,
    estimated_time: datetime,
) -> WeatherPoint:
    cache_key = _cache_key(latitude, longitude, estimated_time)
    cached_point = _weather_cache.get(cache_key)
    if cached_point is not None:
        return cached_point.model_copy()

    response = await _get_http_client().get(
        OPEN_METEO_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "precipitation,wind_speed_10m,weather_code",
            "timezone": "UTC",
            "forecast_days": 7,
            "wind_speed_unit": "kmh",
        },
    )
    response.raise_for_status()
    payload = response.json()
    hourly = payload["hourly"]
    times = hourly["time"]
    if not times:
        raise ValueError("Open-Meteo returned no hourly forecast times")

    selected_index = _nearest_hour_index(times, estimated_time)
    precipitation = float(hourly["precipitation"][selected_index])
    wind_kmh = float(hourly["wind_speed_10m"][selected_index])
    weather_code = int(hourly["weather_code"][selected_index])
    severity = _severity(precipitation, wind_kmh, weather_code)
    point = WeatherPoint(
        lat=latitude,
        lng=longitude,
        time=_parse_forecast_time(times[selected_index]),
        severity=severity,
        summary=f"Rain {precipitation:.1f} mm, wind {wind_kmh:.0f} km/h",
    )
    _weather_cache[cache_key] = point
    return point.model_copy()


def _nearest_hour_index(times: list[str], estimated_time: datetime) -> int:
    forecast_times = [_parse_forecast_time(value) for value in times]
    if _as_utc(estimated_time) > forecast_times[-1]:
        return len(forecast_times) - 1
    return min(
        range(len(forecast_times)),
        key=lambda index: abs((forecast_times[index] - _as_utc(estimated_time)).total_seconds()),
    )


def _parse_forecast_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _as_utc(parsed)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _cache_key(latitude: float, longitude: float, forecast_time: datetime) -> tuple[float, float, str]:
    forecast_hour = _as_utc(forecast_time).replace(minute=0, second=0, microsecond=0)
    return round(latitude, 5), round(longitude, 5), forecast_hour.isoformat()


def _severity(precipitation_mm: float, wind_kmh: float, weather_code: int) -> float:
    weather_code_impact = 1.0 if weather_code >= 95 else 0.5 if weather_code >= 61 else 0.0
    raw_severity = (
        SEVERITY_WEIGHTS["precipitation"] * min(precipitation_mm / 10, 1)
        + SEVERITY_WEIGHTS["wind"] * min(wind_kmh / 60, 1)
        + SEVERITY_WEIGHTS["weather_code"] * weather_code_impact
    )
    return max(0.0, min(raw_severity, 1.0))
