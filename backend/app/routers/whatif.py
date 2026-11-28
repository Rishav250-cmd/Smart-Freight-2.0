"""Mock scenario analysis endpoint."""

from fastapi import APIRouter

from app.schemas import WhatIfRequest, WhatIfResponse
from app.services.mock_contracts import load_mock_response

router = APIRouter(tags=["whatif"])


@router.post(
    "/whatif",
    response_model=WhatIfResponse,
    summary="Mock what-if scenarios",
    description="Returns illustrative rule-based scenarios; no prediction model is connected yet.",
)
async def whatif(request: WhatIfRequest) -> WhatIfResponse:
    """Return the what-if contract example while mock mode is enabled."""
    return load_mock_response("whatif.response.json", WhatIfResponse)
