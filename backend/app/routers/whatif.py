"""Mock scenario analysis endpoint."""

from fastapi import APIRouter

from app.schemas import WhatIfRequest, WhatIfResponse

router = APIRouter(tags=["whatif"])


@router.post(
    "/whatif",
    response_model=WhatIfResponse,
    summary="Mock what-if scenarios",
    description="Returns illustrative rule-based scenarios; no prediction model is connected yet.",
)
async def whatif(request: WhatIfRequest) -> WhatIfResponse:
    scheduled_days = request.assessment.scheduled_days
    baseline = min(100.0, 12.0 + scheduled_days * 1.5)
    return WhatIfResponse(
        simulated=True,
        baseline_delay_pct=round(baseline, 2),
        scenarios=[
            {"name": "add_one_scheduled_day", "simulated_delay_pct": round(max(0, baseline - 5), 2)},
            {"name": "requested_changes", "changes": request.changes, "simulated_delay_pct": round(baseline, 2)},
        ],
    )
