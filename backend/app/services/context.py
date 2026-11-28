"""Placeholder context adjustments for shipment delay risk."""

from collections.abc import Sequence

from app.schemas import ContextAdjustments, RouteInfo, WeatherPoint

# Placeholder percentage-point weights; replace with context_config.json values.
W_WEATHER = 15.0
W_TRAFFIC = 20.0


def calculate_context_adjustments(
    route: RouteInfo,
    weather_points: Sequence[WeatherPoint],
) -> ContextAdjustments:
    """Calculate rule-based signal adjustments in percentage points."""
    max_weather_severity = max(
        (point.severity for point in weather_points),
        default=0.0,
    )
    weather_adjustment = max_weather_severity * W_WEATHER
    traffic_adjustment = max(0.0, route.traffic_ratio - 1.0) * W_TRAFFIC
    return ContextAdjustments(
        weather=weather_adjustment,
        traffic=traffic_adjustment,
        news=0.0,
    )
