"""STUB for the Day 2 XGBoost delay probability model."""

from app.schemas import AssessRequest

_BASE_DELAY_PCT = 25.0
_MODE_RISK_POINTS = {
    "Standard Class": 0.0,
    "Second Class": 4.0,
    "First Class": 10.0,
    "Same Day": 15.0,
}


def predict_base_delay_pct_stub(request: AssessRequest) -> float:
    """Return deterministic placeholder risk; replace with XGBoost on Day 2.

    The result is a probability expressed in percentage points. This simple
    STUB makes faster shipping modes, tighter schedules, and larger quantities
    riskier until the trained model is connected.
    """
    schedule_points = max(-10.0, min(20.0, (3 - request.scheduled_days) * 5.0))
    quantity_points = min(max(request.quantity - 1, 0) * 0.25, 10.0)
    base_delay_pct = (
        _BASE_DELAY_PCT
        + _MODE_RISK_POINTS[request.shipping_mode]
        + schedule_points
        + quantity_points
    )
    return max(5.0, min(base_delay_pct, 95.0))
