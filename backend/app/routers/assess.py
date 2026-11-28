"""Shipment delay risk assessment endpoints."""

from fastapi import APIRouter

from app.config import get_settings
from app.schemas import AssessRequest, AssessResponse, Breakdown
from app.services.context import calculate_context_adjustments
from app.services.mock_contracts import load_mock_response
from app.services.model_stub import predict_base_delay_pct_stub
from app.services.routes import get_route
from app.services.weather import get_route_weather

router = APIRouter(tags=["assessment"])
STATUS_STABLE_MAX_PCT = 35.0  # Placeholder thresholds for product calibration.
STATUS_CAUTION_MAX_PCT = 60.0


@router.post(
    "/assess",
    response_model=AssessResponse,
    summary="Shipment delay risk assessment",
    description=(
        "USE_MOCK=true returns the checked-in contract example. Real mode uses route and weather "
        "services with a deterministic model STUB pending the Day 2 XGBoost integration."
    ),
)
async def assess_shipment(request: AssessRequest) -> AssessResponse:
    """Assess shipment risk using a fixture or the available live signals."""
    if get_settings().use_mock:
        return load_mock_response("assess.response.json", AssessResponse)

    route = await get_route(
        request.origin,
        request.destination,
        request.departure_time,
    )
    try:
        weather_points = await get_route_weather(
            route.polyline,
            request.departure_time,
            route.traffic_min,
        )
    except Exception:
        weather_points = []

    base_delay_pct = predict_base_delay_pct_stub(request)
    adjustments = calculate_context_adjustments(route, weather_points)
    delay_pct = max(
        0.0,
        min(
            base_delay_pct
            + adjustments.weather
            + adjustments.traffic
            + adjustments.news,
            100.0,
        ),
    )
    status = (
        "stable"
        if delay_pct < STATUS_STABLE_MAX_PCT
        else "caution"
        if delay_pct < STATUS_CAUTION_MAX_PCT
        else "critical"
    )
    return AssessResponse(
        delay_pct=delay_pct,
        status=status,
        expected_delay_hours=None,
        breakdown=Breakdown(
            base=base_delay_pct,
            weather=adjustments.weather,
            traffic=adjustments.traffic,
            news=adjustments.news,
        ),
        route=route,
        weather_points=weather_points,
        shap_top5=[],
        signals_available={
            "route_traffic": route.source == "google",
            "weather": bool(weather_points),
            "news": False,
        },
    )
