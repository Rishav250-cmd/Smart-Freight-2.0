"""Shipment delay risk assessment endpoints."""

from fastapi import APIRouter

from app.schemas import (
    AssessRequest,
    AssessResponse,
    Breakdown,
    RouteInfo,
)

router = APIRouter(tags=["assessment"])


@router.post(
    "/assess",
    response_model=AssessResponse,
    summary="Mock delay risk assessment",
    description="Returns a deterministic mock assessment until prediction and signal services are connected.",
)
async def assess_shipment(request: AssessRequest) -> AssessResponse:
    """Return a clearly documented mock assessment for the supplied shipment."""
    distance_km = _haversine_km(
        request.origin.lat,
        request.origin.lng,
        request.destination.lat,
        request.destination.lng,
    )
    delay_pct = min(100.0, 12.0 + (distance_km / 250.0) + request.scheduled_days * 1.5)
    status = "stable" if delay_pct < 35 else "caution" if delay_pct < 70 else "critical"
    return AssessResponse(
        delay_pct=round(delay_pct, 2),
        status=status,
        expected_delay_hours=round(delay_pct / 20, 2),
        breakdown=Breakdown(
            base=round(delay_pct, 2), weather=0.0, traffic=0.0, news=0.0
        ),
        route=RouteInfo(
            distance_km=round(distance_km, 2),
            normal_min=0.0,
            traffic_min=0.0,
            traffic_ratio=1.0,
            polyline="",
            source="osrm",
        ),
        weather_points=[],
        shap_top5=[],
        signals_available={"route_traffic": False, "weather": False, "news": False},
    )


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Compute straight-line distance for the mock response."""
    from math import asin, cos, radians, sin, sqrt

    lat1_rad, lat2_rad = radians(lat1), radians(lat2)
    delta_lat, delta_lng = radians(lat2 - lat1), radians(lng2 - lng1)
    value = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(value))
