"""Shipment delay risk assessment endpoints."""

from fastapi import APIRouter

from app.schemas import (
    AssessRequest,
    AssessResponse,
)
from app.services.mock_contracts import load_mock_response

router = APIRouter(tags=["assessment"])


@router.post(
    "/assess",
    response_model=AssessResponse,
    summary="Mock delay risk assessment",
    description="Returns a deterministic mock assessment until prediction and signal services are connected.",
)
async def assess_shipment(request: AssessRequest) -> AssessResponse:
    """Return the sample rule-based assessment while mock mode is enabled."""
    return load_mock_response("assess.response.json", AssessResponse)
