from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="UI_")

    # internal address of the API (the browser never talks to it directly in development)
    api_url: str = "http://localhost:8000"
    default_language: str = "de"
    public_base_url: str = "http://localhost:8080"
    api_timeout_seconds: float = 20.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
