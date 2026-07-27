"""Tests for mcp-gateway FastAPI application metadata."""

from mcp_gateway.main import app


def test_app_title_contains_mcp():
    assert "MCP" in app.title


def test_app_version():
    assert app.version == "0.1.0"


async def test_openapi_json_endpoint(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    assert "MCP" in r.json()["info"]["title"]
