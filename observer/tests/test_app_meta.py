"""Tests for observer FastAPI application metadata."""

from observer.main import app


def test_app_title_contains_observer():
    assert "Observer" in app.title


def test_app_version():
    assert app.version == "0.1.0"


async def test_openapi_json_endpoint(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    assert "Observer" in r.json()["info"]["title"]
