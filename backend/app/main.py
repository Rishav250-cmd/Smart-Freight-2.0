"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import analytics, assess, history, recommend, track, whatif
from app.schemas import HealthResponse
from app.services.routes import close_route_client
from app.services.weather import close_weather_client

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Close shared route and weather HTTP clients when the app shuts down."""
    yield
    await close_route_client()
    await close_weather_client()


app = FastAPI(
    title="SmartFreight API",
    description="Shipment delay risk API. Endpoints marked mock return simulated or rule-based data.",
    version="0.1.0",
    lifespan=lifespan,
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


@app.get("/health", response_model=HealthResponse, tags=["health"], summary="Health check")
async def health() -> HealthResponse:
    """Report that the API process is responding."""
    return HealthResponse(status="ok")
