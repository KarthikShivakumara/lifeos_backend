from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "LifeOS API"
    environment: str = "development"
    secret_key: str = "change-me-production-secret-must-be-at-least-32-chars-long"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./lifeos.db"
    cors_origins: str = "http://localhost:3000,https://lifeos.health"
    gemini_api_key: str = ""
    ml_model_dir: str = "./models"
    openai_api_key: str = ""

    # Database Connection Pool Settings for Production (PostgreSQL / SQLite)
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ["production", "prod"]

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_production_secrets(self) -> None:
        """Validate production configuration parameters to prevent insecure deployments."""
        if self.is_production:
            if self.secret_key in ["change-me", "secret", "default", "123456"] or len(self.secret_key) < 32:
                raise ValueError("CRITICAL: Secret key must be a secure random string of at least 32 characters in production.")
            if "*" in self.cors_origin_list:
                raise ValueError("CRITICAL: Wildcard CORS origin '*' is strictly prohibited in production mode.")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production:
        settings.validate_production_secrets()
    return settings
