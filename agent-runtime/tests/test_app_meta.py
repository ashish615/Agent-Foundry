"""Tests for agent-runtime FastAPI application metadata."""

from agent_runtime.main import app


def test_app_title_contains_agent():
    assert "Agent" in app.title


def test_app_version():
    assert app.version == "0.1.0"


async def test_openapi_json_endpoint(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    assert "Agent" in r.json()["info"]["title"]
