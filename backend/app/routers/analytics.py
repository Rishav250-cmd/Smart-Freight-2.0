"""Mock analytics endpoints."""

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/summary",
    response_model=dict[str, Any],
    summary="Mock analytics summary",
    description="Returns illustrative aggregate metrics until analytics storage is connected.",
)
async def summary() -> dict[str, Any]:
    return {"simulated": True, "shipment_count": 0, "average_delay_pct": None}


@router.get(
    "/trends",
    response_model=dict[str, Any],
    summary="Mock analytics trends",
    description="Returns empty illustrative trend data until analytics storage is connected.",
)
async def trends() -> dict[str, Any]:
    return {"simulated": True, "points": []}
