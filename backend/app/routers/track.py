"""Mock shipment tracking endpoint."""

from fastapi import APIRouter

from app.schemas import TrackResponse

router = APIRouter(tags=["tracking"])


@router.get(
    "/track/{shipment_id}",
    response_model=TrackResponse,
    summary="Mock shipment tracking",
    description="Returns illustrative tracking status until a tracking provider is connected.",
)
async def track_shipment(shipment_id: str) -> TrackResponse:
    return TrackResponse(
        shipment_id=shipment_id,
        simulated=True,
        status="tracking_unavailable",
        events=[],
    )
