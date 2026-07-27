"""Tests for model-registry FastAPI application metadata."""

from model_registry.main import app


def test_app_title_contains_model_registry():
    assert "Model Registry" in app.title


def test_app_version():
    assert app.version == "0.1.0"


async def test_openapi_json_endpoint(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    assert "Model Registry" in r.json()["info"]["title"]


async def test_docs_endpoint_available(client):
    r = await client.get("/docs")
    assert r.status_code == 200
