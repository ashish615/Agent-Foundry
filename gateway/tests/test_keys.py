"""Tests for API key CRUD endpoints."""

import pytest

from .conftest import KEY_ID, USER_ID, db_result, make_api_key, make_user, refresh_side_effect


# ---------------------------------------------------------------------------
# GET /v1/users/{user_id}/api-keys
# ---------------------------------------------------------------------------

async def test_list_keys_no_auth_401(client):
    r = await client.get(f"/v1/users/{USER_ID}/api-keys")
    assert r.status_code == 401


async def test_list_keys_own_user_returns_keys(db_client, admin_token):
    client, mock_db = db_client
    key = make_api_key(scopes=["completions"])
    mock_db.execute.side_effect = [
        db_result(scalar=make_user()),   # get_current_user
        db_result(rows=[key]),           # ApiKey query
    ]

    r = await client.get(
        f"/v1/users/{USER_ID}/api-keys",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert "plaintext_key" not in data[0]   # plaintext NEVER returned on list
    assert data[0]["scopes"] == ["completions"]


async def test_list_keys_other_user_non_admin_403(db_client, admin_token):
    import uuid
    client, mock_db = db_client
    other = uuid.uuid4()
    # Return a member-role user so _assert_own_or_admin raises 403
    mock_db.execute.side_effect = [db_result(scalar=make_user(role="member"))]

    r = await client.get(
        f"/v1/users/{other}/api-keys",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # admin_token carries scopes=["*"] but user.role="member" → the role check fails
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /v1/users/{user_id}/api-keys
# ---------------------------------------------------------------------------

async def test_create_key_requires_keys_write_scope(db_client, member_token):
    client, mock_db = db_client
    mock_db.execute.side_effect = [db_result(scalar=make_user(role="member"))]

    r = await client.post(
        f"/v1/users/{USER_ID}/api-keys",
        json={"scopes": ["completions"]},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert r.status_code == 403


async def test_create_key_returns_plaintext_once(db_client, admin_token):
    client, mock_db = db_client
    mock_user = make_user()
    mock_db.execute.side_effect = [
        db_result(scalar=mock_user),   # get_current_user
        db_result(scalar=mock_user),   # target user exists check
    ]
    mock_db.refresh.side_effect = refresh_side_effect()

    r = await client.post(
        f"/v1/users/{USER_ID}/api-keys",
        json={"scopes": ["completions"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert "plaintext_key" in data
    assert data["plaintext_key"].startswith("af-")
    assert data["scopes"] == ["completions"]


async def test_create_key_user_not_found_404(db_client, admin_token):
    import uuid
    client, mock_db = db_client
    mock_db.execute.side_effect = [
        db_result(scalar=make_user()),   # get_current_user
        db_result(scalar=None),          # target user not found
    ]

    r = await client.post(
        f"/v1/users/{uuid.uuid4()}/api-keys",
        json={"scopes": ["completions"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /v1/users/{user_id}/api-keys/{key_id}
# ---------------------------------------------------------------------------

async def test_delete_key_not_found_404(db_client, admin_token):
    import uuid
    client, mock_db = db_client
    mock_db.execute.side_effect = [
        db_result(scalar=make_user()),  # get_current_user
        db_result(scalar=None),         # key not found
    ]

    r = await client.delete(
        f"/v1/users/{USER_ID}/api-keys/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404


async def test_delete_key_success_204(db_client, admin_token):
    client, mock_db = db_client
    key = make_api_key()
    mock_db.execute.side_effect = [
        db_result(scalar=make_user()),  # get_current_user
        db_result(scalar=key),          # key found
    ]

    r = await client.delete(
        f"/v1/users/{USER_ID}/api-keys/{KEY_ID}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 204
