from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "axiom-console"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./axiom.db"

    # Security
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Demo mode (explicit opt-in only)
    demo_mode: bool = False

    # Keycloak (configured by operator)
    keycloak_url: Optional[str] = None
    keycloak_realm: Optional[str] = None
    keycloak_client_id: Optional[str] = None
    keycloak_client_secret: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()