# ABOUTME: App configuration via environment variables and .env file.
# ABOUTME: Uses pydantic-settings for typed config with sensible defaults.
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    database_url: str = "sqlite+aiosqlite:///data/adhdaf.db"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"
    capture_token: str = "change-me-to-a-random-secret"
    admin_token: str = "change-me-to-a-different-secret"
    apprise_urls: str = ""
    host: str = "127.0.0.1"
    port: int = 1738


settings = Settings()
