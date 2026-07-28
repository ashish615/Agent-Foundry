from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODEL_REGISTRY_", env_file=".env")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_foundry"
    cors_origins: list[str] = ["*"]
