"""Tests for GET /v1/health — gateway service."""


async def test_health_status_200(client):
    r = await client.get("/v1/health")
    assert r.status_code == 200


async def test_health_body(client):
    r = await client.get("/v1/health")
    assert r.json() == {"status": "ok", "service": "gateway"}


async def test_health_content_type_json(client):
    r = await client.get("/v1/health")
    assert "application/json" in r.headers["content-type"]


async def test_health_unknown_path_returns_404(client):
    r = await client.get("/v1/does-not-exist")
    assert r.status_code == 404


async def test_health_post_not_allowed(client):
    r = await client.post("/v1/health")
    assert r.status_code == 405
