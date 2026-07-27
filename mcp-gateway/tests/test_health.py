"""Tests for GET /v1/health — mcp-gateway service."""


async def test_health_status_200(client):
    r = await client.get("/v1/health")
    assert r.status_code == 200


async def test_health_body(client):
    r = await client.get("/v1/health")
    assert r.json() == {"status": "ok", "service": "mcp-gateway"}


async def test_health_content_type_json(client):
    r = await client.get("/v1/health")
    assert "application/json" in r.headers["content-type"]


async def test_unknown_path_returns_404(client):
    r = await client.get("/v1/unknown")
    assert r.status_code == 404


async def test_post_to_health_not_allowed(client):
    r = await client.post("/v1/health")
    assert r.status_code == 405
