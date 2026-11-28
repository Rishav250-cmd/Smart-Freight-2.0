"""Mock shipment recommendations endpoint."""

from fastapi import APIRouter

from app.schemas import RecommendRequest, RecommendResponse

router = APIRouter(tags=["recommendations"])


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    summary="Mock shipment recommendations",
    description="Returns illustrative rule-based recommendations; no optimization service is connected yet.",
)
async def recommend(request: RecommendRequest) -> RecommendResponse:
    return RecommendResponse(
        simulated=True,
        recommendations=[
            {
                "action": "review_scheduled_days",
                "reason": "Mock recommendation based on the submitted schedule.",
                "scheduled_days": request.assessment.scheduled_days,
            }
        ],
    )
