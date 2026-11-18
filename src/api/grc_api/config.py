"""Settings from environment variables (documented in .env.example)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="postgresql+psycopg://grc:grc@localhost:5432/grc")
    public_base_url: str = "http://localhost:8080"
    session_ttl_hours: int = 12
    # Demo sign-in: choose a person without password (prototype phase). Turn off in production.
    demo_login: bool = True
    bootstrap_admin_user: str = ""
    bootstrap_admin_password: str = ""
    # Load the demo data at start when the database is empty.
    seed_demo_on_empty: bool = False
    log_level: str = "INFO"
    # encrypts secrets stored in the database (AI API key); changing it makes them unreadable
    settings_secret: str = ""

    @property
    def secure_cookies(self) -> bool:
        return self.public_base_url.startswith("https://")


@lru_cache
def get_settings() -> Settings:
    return Settings()
