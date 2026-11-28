"""Route lookup with Google Routes API and OSRM fallback."""

from datetime import datetime, timezone
from functools import lru_cache

import httpx
from cachetools import TTLCache

from app.config import get_settings
from app.schemas import Place, RouteInfo

GOOGLE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
GOOGLE_FIELD_MASK = (
    "routes.duration,routes.staticDuration,routes.distanceMeters,"
    "routes.polyline.encodedPolyline"
)
REQUEST_TIMEOUT_SECONDS = 5.0
CACHE_MAXSIZE = 1024

_route_cache: TTLCache[tuple[float, float, float, float, str], RouteInfo] = TTLCache(
    maxsize=CACHE_MAXSIZE,
    ttl=get_settings().cache_ttl_seconds,
)


@lru_cache(maxsize=1)
def _get_http_client() -> httpx.AsyncClient:
    """Return the shared HTTP client used for Google and OSRM requests."""
    timeout = httpx.Timeout(REQUEST_TIMEOUT_SECONDS)
    return httpx.AsyncClient(timeout=timeout)


async def close_route_client() -> None:
    """Close and clear the shared client during application shutdown."""
    if _get_http_client.cache_info().currsize:
        await _get_http_client().aclose()
        _get_http_client.cache_clear()


def clear_route_cache() -> None:
    """Clear cached routes, primarily for tests and explicit cache resets."""
    _route_cache.clear()


async def get_route(
    origin: Place,
    destination: Place,
    departure_time: datetime,
) -> RouteInfo:
    """Get a traffic-aware route, falling back to a normal OSRM route."""
    settings = get_settings()
    cache_key = _cache_key(origin, destination, departure_time)
    cached_route = _route_cache.get(cache_key)
    if cached_route is not None:
        return cached_route.model_copy()

    route: RouteInfo
    if settings.google_maps_server_key:
        try:
            route = await _get_google_route(
                origin,
                destination,
                departure_time,
                settings.google_maps_server_key,
            )
        except Exception:
            route = await _get_osrm_route(origin, destination)
    else:
        route = await _get_osrm_route(origin, destination)

    _route_cache[cache_key] = route
    return route.model_copy()


async def _get_google_route(
    origin: Place,
    destination: Place,
    departure_time: datetime,
    api_key: str,
) -> RouteInfo:
    departure = _as_utc(departure_time)
    now = datetime.now(timezone.utc)
    if departure < now:
        departure = now

    response = await _get_http_client().post(
        GOOGLE_ROUTES_URL,
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": GOOGLE_FIELD_MASK,
        },
        json={
            "origin": {
                "location": {
                    "latLng": {"latitude": origin.lat, "longitude": origin.lng}
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": destination.lat,
                        "longitude": destination.lng,
                    }
                }
            },
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE",
            "departureTime": _rfc3339(departure),
        },
    )
    response.raise_for_status()
    payload = response.json()
    route = payload["routes"][0]
    normal_min = _duration_minutes(route["staticDuration"])
    traffic_min = _duration_minutes(route["duration"])
    return RouteInfo(
        distance_km=float(route["distanceMeters"]) / 1000,
        normal_min=normal_min,
        traffic_min=traffic_min,
        traffic_ratio=traffic_min / normal_min if normal_min else 1.0,
        polyline=route["polyline"]["encodedPolyline"],
        source="google",
    )


async def _get_osrm_route(origin: Place, destination: Place) -> RouteInfo:
    url = (
        f"{OSRM_ROUTE_URL}/{origin.lng},{origin.lat};"
        f"{destination.lng},{destination.lat}"
    )
    response = await _get_http_client().get(
        url,
        params={"overview": "full", "geometries": "polyline"},
    )
    response.raise_for_status()
    payload = response.json()
    routes = payload.get("routes", [])
    if payload.get("code") != "Ok" or not routes:
        raise RuntimeError("OSRM did not return a route")

    route = routes[0]
    normal_min = float(route["duration"]) / 60
    return RouteInfo(
        distance_km=float(route["distance"]) / 1000,
        normal_min=normal_min,
        traffic_min=normal_min,
        traffic_ratio=1.0,
        polyline=route["geometry"],
        source="osrm",
    )


def _cache_key(
    origin: Place,
    destination: Place,
    departure_time: datetime,
) -> tuple[float, float, float, float, str]:
    departure_hour = _as_utc(departure_time).replace(
        minute=0, second=0, microsecond=0
    )
    return (
        round(origin.lat, 5),
        round(origin.lng, 5),
        round(destination.lat, 5),
        round(destination.lng, 5),
        departure_hour.isoformat(),
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _rfc3339(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _duration_minutes(value: str) -> float:
    """Convert a protobuf Duration string such as ``"123.5s"`` to minutes."""
    if not value.endswith("s"):
        raise ValueError("Google duration must use protobuf seconds format")
    return float(value[:-1]) / 60
