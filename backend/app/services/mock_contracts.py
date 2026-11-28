"""Load and validate response examples used by mock API handlers."""

from pathlib import Path
from typing import TypeVar

from fastapi import HTTPException
from pydantic import BaseModel

from app.config import get_settings

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
CONTRACTS_DIR = Path(__file__).resolve().parents[3] / "contracts"


def load_mock_response(filename: str, response_model: type[ResponseModel]) -> ResponseModel:
    """Read a contract response and validate it with the endpoint's schema."""
    if not get_settings().use_mock:
        raise HTTPException(status_code=501, detail="Live service is not configured")

    contract_path = CONTRACTS_DIR / filename
    try:
        contract_json = contract_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Unable to load mock contract: {contract_path}") from exc
    try:
        return response_model.model_validate_json(contract_json)
    except ValueError as exc:
        raise RuntimeError(
            f"Mock contract {filename} does not match {response_model.__name__}"
        ) from exc
