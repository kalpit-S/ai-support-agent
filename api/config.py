from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql://support:support_dev@db:5432/support_db"
    redis_url: str = "redis://redis:6379/0"
    batch_window_seconds: int = 5
    api_title: str = "AI Support Agent API"
    api_version: str = "0.1.0"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
