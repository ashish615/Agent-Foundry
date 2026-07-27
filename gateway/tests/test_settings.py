"""Tests for gateway Settings (pydantic-settings)."""

import pytest
from gateway.settings import Settings


def test_default_database_url():
    s = Settings()
    assert s.database_url.startswith("postgresql+asyncpg://")


def test_default_redis_url():
    s = Settings()
    assert s.redis_url.startswith("redis://")


def test_default_cors_origins_wildcard():
    s = Settings()
    assert s.cors_origins == ["*"]


def test_default_otlp_endpoint():
    s = Settings()
    assert s.otlp_endpoint == "http://localhost:4317"


def test_default_secret_key_not_empty():
    s = Settings()
    assert len(s.secret_key) > 0


def test_env_prefix_overrides_secret_key(monkeypatch):
    monkeypatch.setenv("GATEWAY_SECRET_KEY", "super-secret-123")
    s = Settings()
    assert s.secret_key == "super-secret-123"


def test_env_prefix_overrides_redis_url(monkeypatch):
    monkeypatch.setenv("GATEWAY_REDIS_URL", "redis://redis-host:6380/2")
    s = Settings()
    assert s.redis_url == "redis://redis-host:6380/2"


def test_env_prefix_overrides_database_url(monkeypatch):
    monkeypatch.setenv("GATEWAY_DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/mydb")
    s = Settings()
    assert "mydb" in s.database_url


def test_cors_origins_can_be_list_of_domains(monkeypatch):
    monkeypatch.setenv("GATEWAY_CORS_ORIGINS", '["https://app.example.com","https://admin.example.com"]')
    s = Settings()
    assert "https://app.example.com" in s.cors_origins
    assert "https://admin.example.com" in s.cors_origins
