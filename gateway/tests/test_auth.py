"""Tests for POST /v1/auth/token and auth middleware (JWT + API key)."""

import hashlib

import pytest

from .conftest import KEY_ID, ORG_ID, USER_ID, db_result, make_api_key, make_org, make_user, refresh_side_effect


# ---------------------------------------------------------------------------
# POST /v1/auth/token
# ---------------------------------------------------------------------------

async def test_token_invalid_key_returns_401(db_client):
    client, mock_db = db_client
    mock_db.execute.side_effect = [db_result(scalar=None)]  # key not found

    r = await client.post("/v1/auth/token", json={"api_key": "af-notavalidkey"})
    assert r.status_code == 401


async def test_token_valid_key_returns_jwt(db_client):
    client, mock_db = db_client
    mock_key = make_api_key(scopes=["*"])
    mock_user = make_user()
    mock_db.execute.side_effect = [
        db_result(scalar=mock_key),
        db_result(scalar=mock_user),
    ]

    r = await client.post("/v1/auth/token", json={"api_key": "af-somevalidkey"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert body["expires_in"] == 3600


async def test_token_missing_body_returns_422(db_client):
    client, _ = db_client
    r = await client.post("/v1/auth/token", json={})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Auth middleware — unauthenticated requests
# ---------------------------------------------------------------------------

async def test_protected_route_no_auth_returns_401(client):
    r = await client.get("/v1/orgs")
    assert r.status_code == 401


async def test_protected_route_bad_jwt_returns_401(client):
    r = await client.get("/v1/orgs", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Auth middleware — valid JWT grants access
# ---------------------------------------------------------------------------

async def test_protected_route_valid_jwt_resolves_user(db_client, admin_token):
    client, mock_db = db_client
    mock_user = make_user()
    # get_current_user queries User by id from JWT sub
    mock_db.execute.side_effect = [
        db_result(scalar=mock_user),           # User lookup (get_current_user)
        db_result(rows=[make_org()]),           # list_orgs query
    ]

    r = await client.get("/v1/orgs", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Scope enforcement
# ---------------------------------------------------------------------------

async def test_member_token_cannot_create_org(db_client, member_token):
    client, mock_db = db_client
    mock_user = make_user(role="member", scopes=["completions"])
    mock_db.execute.side_effect = [db_result(scalar=mock_user)]

    r = await client.post(
        "/v1/orgs",
        json={"name": "New Org", "slug": "new-org"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert r.status_code == 403


async def test_admin_token_can_create_org(db_client, admin_token):
    client, mock_db = db_client
    mock_db.execute.side_effect = [
        db_result(scalar=make_user(role="admin")),  # get_current_user
    ]
    mock_db.refresh.side_effect = refresh_side_effect()

    r = await client.post(
        "/v1/orgs",
        json={"name": "New Org", "slug": "new-org"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201
    assert r.json()["slug"] == "new-org"
