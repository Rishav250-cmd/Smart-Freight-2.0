"""Pydantic request and response models for the SmartFreight API."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class APIModel(BaseModel):
    """Shared schema settings for stable OpenAPI names and JSON serialization."""

    model_config = ConfigDict(extra="forbid")


class Place(APIModel):
    name: str
    lat: float
    lng: float


class AssessRequest(APIModel):
    origin: Place
    destination: Place
    departure_time: datetime
    shipping_mode: Literal["Standard Class", "Second Class", "First Class", "Same Day"]
    scheduled_days: int = Field(ge=0)
    quantity: int = Field(ge=1)
    order_value: float = Field(ge=0)
    department: str

    @model_validator(mode="after")
    def require_transit_time_for_intercity_route(self) -> "AssessRequest":
        same_coordinates = (
            self.origin.lat == self.destination.lat
            and self.origin.lng == self.destination.lng
        )
        if not same_coordinates and self.scheduled_days < 1:
            raise ValueError(
                "scheduled_days must be at least 1 when origin and destination are different places"
            )
        return self


class RouteInfo(APIModel):
    distance_km: float
    normal_min: float
    traffic_min: float
    traffic_ratio: float
    polyline: str
    source: Literal["google", "osrm"]


class WeatherPoint(APIModel):
    lat: float
    lng: float
    time: datetime
    severity: float = Field(ge=0, le=1)
    summary: str


class Breakdown(APIModel):
    """Delay attribution in percentage points."""

    base: float
    weather: float
    traffic: float
    news: float


class ShapFactor(APIModel):
    feature: str
    impact: float


class AssessResponse(APIModel):
    delay_pct: float = Field(ge=0, le=100)
    status: Literal["stable", "caution", "critical"]
    expected_delay_hours: float | None
    breakdown: Breakdown
    route: RouteInfo
    weather_points: list[WeatherPoint]
    shap_top5: list[ShapFactor]
    signals_available: dict[Literal["route_traffic", "weather", "news"], bool]


class WhatIfRequest(APIModel):
    assessment: AssessRequest
    changes: dict[str, Any] = Field(default_factory=dict)


class WhatIfResponse(APIModel):
    simulated: bool
    baseline_delay_pct: float = Field(ge=0, le=100)
    scenarios: list[dict[str, Any]]


class RecommendRequest(APIModel):
    assessment: AssessRequest


class RecommendResponse(APIModel):
    simulated: bool
    recommendations: list[dict[str, Any]]


class HistoryResponse(APIModel):
    simulated: bool
    items: list[dict[str, Any]]


class TrackResponse(APIModel):
    shipment_id: str
    simulated: bool
    status: str
    events: list[dict[str, Any]]


AnalyticsResponse = dict[str, Any]
