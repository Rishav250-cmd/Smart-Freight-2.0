"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import analytics, assess, history, recommend, track, whatif

settings = get_settings()

app = FastAPI(
    title="SmartFreight API",
    description="Shipment delay risk API. Endpoints marked mock return simulated or rule-based data.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(["http://localhost:3000", *settings.allowed_origins])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assess.router)
app.include_router(whatif.router)
app.include_router(recommend.router)
app.include_router(history.router)
app.include_router(track.router)
app.include_router(analytics.router)


@app.get("/health", tags=["health"], summary="Health check")
async def health() -> dict[str, str]:
    """Report that the API process is responding."""
    return {"status": "ok"}
