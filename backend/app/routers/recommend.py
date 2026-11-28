"""Mock shipment recommendations endpoint."""

from fastapi import APIRouter

from app.schemas import RecommendResponse
from app.services.mock_contracts import load_mock_response

router = APIRouter(tags=["recommendations"])


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    summary="Mock shipment recommendations",
    description="Returns illustrative rule-based recommendations; no optimization service is connected yet.",
)
async def recommend() -> RecommendResponse:
    """Return mock recommendation data from its contract example."""
    return load_mock_response("recommend.response.json", RecommendResponse)
