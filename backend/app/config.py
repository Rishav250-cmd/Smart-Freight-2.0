"""Application settings loaded from environment variables or a local .env file."""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API."""

    use_mock: bool = True
    google_maps_server_key: str | None = None
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    cache_ttl_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        """Accept a comma-separated origin list from the environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cache_ttl_seconds")
    @classmethod
    def validate_cache_ttl(cls, value: int) -> int:
        if value < 0:
            raise ValueError("CACHE_TTL_SECONDS must be zero or greater")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings; this is the application's configuration cache."""
    return Settings()
