from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Worker configuration loaded from environment variables."""

    database_url: str = "postgresql://support:support_dev@db:5432/support_db"
    redis_url: str = "redis://redis:6379/0"
    batch_window_seconds: int = 5
    poll_interval_seconds: float = 1.0
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-4.5"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
