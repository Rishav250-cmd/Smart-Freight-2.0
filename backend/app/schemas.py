"""Pydantic request and response models for the SmartFreight API."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator


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


class ContextAdjustments(APIModel):
    """Contextual changes to delay risk, measured in percentage points."""

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


class HealthResponse(APIModel):
    status: Literal["ok"]


class WhatIfRequest(APIModel):
    assessment: AssessRequest
    changes: dict[str, Any] = Field(default_factory=dict)


class WhatIfResponse(APIModel):
    simulated: bool
    baseline_delay_pct: float = Field(ge=0, le=100)
    scenarios: list[dict[str, Any]]


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


class ThresholdHistogram(APIModel):
    bins: list[float]
    late: list[int]
    on_time: list[int]

    @model_validator(mode="after")
    def arrays_have_equal_length(self) -> "ThresholdHistogram":
        if not (len(self.bins) == len(self.late) == len(self.on_time)):
            raise ValueError("score_histogram bins, late, and on_time arrays must have equal length")
        return self


class ThresholdAnalytics(APIModel):
    thresholds: list[float]
    precision: list[float]
    recall: list[float]
    f1: list[float]
    flagged: list[int]
    score_histogram: ThresholdHistogram

    @model_validator(mode="after")
    def arrays_have_equal_length(self) -> "ThresholdAnalytics":
        lengths = {len(self.thresholds), len(self.precision), len(self.recall), len(self.f1), len(self.flagged)}
        if len(lengths) != 1:
            raise ValueError("thresholds, precision, recall, f1, and flagged arrays must have equal length")
        return self


class ImpactAnalytics(APIModel):
    assumed_penalty_per_breach: float
    breaches_before: int
    breaches_after: int
    saved: float
    is_simulation: Literal[True]


class LaneMetric(APIModel):
    region: str
    shipping_mode: str
    late_rate: float
    avg_predicted_risk: float
    n: int


class LanesAnalytics(RootModel[list[LaneMetric]]):
    """Analytics lane rows."""


class ShapFeature(APIModel):
    feature: str
    mean_abs_shap: float


class ShapAnalytics(RootModel[list[ShapFeature]]):
    """Ranked aggregate SHAP values."""


class CalibrationAnalytics(APIModel):
    bin_mean_predicted: list[float]
    bin_fraction_positive: list[float]
    brier: float

    @model_validator(mode="after")
    def calibration_bins_have_equal_length(self) -> "CalibrationAnalytics":
        if len(self.bin_mean_predicted) != len(self.bin_fraction_positive):
            raise ValueError("calibration bin arrays must have equal length")
        return self
