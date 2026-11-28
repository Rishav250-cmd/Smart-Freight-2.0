"""Mock shipment assessment history endpoint."""

from fastapi import APIRouter

from app.schemas import HistoryResponse

router = APIRouter(tags=["history"])


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Mock assessment history",
    description="Returns an empty mock history until persistence is connected.",
)
async def get_history() -> HistoryResponse:
    return HistoryResponse(simulated=True, items=[])
