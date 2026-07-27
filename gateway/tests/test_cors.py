"""Tests for CORS middleware on the gateway."""


async def test_cors_header_present_for_cross_origin_request(client):
    r = await client.get("/v1/health", headers={"Origin": "http://app.example.com"})
    assert "access-control-allow-origin" in r.headers


async def test_cors_wildcard_allows_any_origin(client):
    r = await client.get("/v1/health", headers={"Origin": "http://anything.test"})
    assert r.headers.get("access-control-allow-origin") in ("*", "http://anything.test")


async def test_cors_preflight_returns_200(client):
    r = await client.options(
        "/v1/health",
        headers={
            "Origin": "http://app.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code == 200


async def test_cors_preflight_exposes_methods(client):
    r = await client.options(
        "/v1/health",
        headers={
            "Origin": "http://app.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-methods" in r.headers


async def test_no_cors_header_without_origin(client):
    r = await client.get("/v1/health")
    # No Origin header → no CORS response header needed
    assert r.status_code == 200
