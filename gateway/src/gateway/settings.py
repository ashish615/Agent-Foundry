from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GATEWAY_", env_file=".env")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_foundry"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["*"]
    otlp_endpoint: str = "http://localhost:4317"
    secret_key: str = "change-me-in-production"
