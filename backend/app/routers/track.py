"""Mock shipment tracking endpoint."""

from fastapi import APIRouter

from app.schemas import TrackResponse
from app.services.mock_contracts import load_mock_response

router = APIRouter(tags=["tracking"])


@router.get(
    "/track/{id}",
    response_model=TrackResponse,
    summary="Mock shipment tracking",
    description="Returns illustrative tracking status until a tracking provider is connected.",
)
async def track_shipment(id: str) -> TrackResponse:
    """Return the static tracking example from its contract in mock mode."""
    return load_mock_response("track.response.json", TrackResponse)
