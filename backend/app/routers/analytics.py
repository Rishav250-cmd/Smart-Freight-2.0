"""Mock analytics endpoints."""

from fastapi import APIRouter

from app.schemas import (
    CalibrationAnalytics,
    ImpactAnalytics,
    LanesAnalytics,
    ShapAnalytics,
    ThresholdAnalytics,
)
from app.services.mock_contracts import load_mock_response

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/threshold",
    response_model=ThresholdAnalytics,
    summary="Mock threshold analytics",
    description="Returns simulated example metrics loaded from the analytics threshold contract.",
)
async def threshold() -> ThresholdAnalytics:
    return load_mock_response("analytics.threshold.json", ThresholdAnalytics)


@router.get(
    "/impact",
    response_model=ImpactAnalytics,
    summary="Mock impact analytics",
    description="Returns simulated impact estimates loaded from the analytics impact contract.",
)
async def impact() -> ImpactAnalytics:
    return load_mock_response("analytics.impact.json", ImpactAnalytics)


@router.get(
    "/lanes",
    response_model=LanesAnalytics,
    summary="Mock lane analytics",
    description="Returns simulated lane metrics loaded from the analytics lanes contract.",
)
async def lanes() -> LanesAnalytics:
    return load_mock_response("analytics.lanes.json", LanesAnalytics)


@router.get(
    "/shap",
    response_model=ShapAnalytics,
    summary="Mock SHAP analytics",
    description="Returns simulated aggregate feature impacts loaded from the analytics SHAP contract.",
)
async def shap() -> ShapAnalytics:
    return load_mock_response("analytics.shap.json", ShapAnalytics)


@router.get(
    "/calibration",
    response_model=CalibrationAnalytics,
    summary="Mock calibration analytics",
    description="Returns simulated calibration metrics loaded from the analytics calibration contract.",
)
async def calibration() -> CalibrationAnalytics:
    return load_mock_response("analytics.calibration.json", CalibrationAnalytics)
