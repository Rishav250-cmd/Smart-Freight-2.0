"""Mock shipment assessment history endpoint."""

from fastapi import APIRouter

from app.schemas import HistoryResponse
from app.services.mock_contracts import load_mock_response

router = APIRouter(tags=["history"])


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Mock assessment history",
    description="Returns an empty mock history until persistence is connected.",
)
async def get_history() -> HistoryResponse:
    """Return the history contract example while mock mode is enabled."""
    return load_mock_response("history.response.json", HistoryResponse)
