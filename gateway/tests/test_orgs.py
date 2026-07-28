"""Tests for GET/POST /v1/orgs and project sub-resources."""

import pytest

from .conftest import ORG_ID, USER_ID, db_result, make_org, make_project, make_user


# ---------------------------------------------------------------------------
# GET /v1/orgs
# ---------------------------------------------------------------------------

async def test_list_orgs_no_auth_401(client):
    r = await client.get("/v1/orgs")
    assert r.status_code == 401


async def test_list_orgs_returns_users_own_org(db_client, admin_token):
    client, mock_db = db_client
    org = make_org()
    mock_db.execute.side_effect = [
        db_result(scalar=make_user()),   # get_current_user
        db_result(rows=[org]),           # list_orgs query
    ]

    r = await client.get("/v1/orgs", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["slug"] == "acme"


async def test_list_orgs_empty_when_no_orgs(db_client, admin_token):
    client, mock_db = db_client
    mock_db.execute.side_effect = [
        db_result(scalar=make_user()),
        db_result(rows=[]),
    ]

    r = await client.get("/v1/orgs", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# POST /v1/orgs  (requires org:admin scope)
# ---------------------------------------------------------------------------

async def test_create_org_requires_org_admin_scope(db_client, member_token):
    client, mock_db = db_client
    mock_db.execute.side_effect = [db_result(scalar=make_user(role="member"))]

    r = await client.post(
        "/v1/orgs",
        json={"name": "Evil Corp", "slug": "evil"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert r.status_code == 403


async def test_create_org_validates_body(db_client, admin_token):
    client, mock_db = db_client
    r = await client.post(
        "/v1/orgs",
        json={"name": "Missing Slug"},   # slug is required
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /v1/orgs/{org_id}/projects
# ---------------------------------------------------------------------------

async def test_list_projects_no_auth_401(client):
    r = await client.get(f"/v1/orgs/{ORG_ID}/projects")
    assert r.status_code == 401


async def test_list_projects_wrong_org_403(db_client, admin_token):
    import uuid
    client, mock_db = db_client
    other_org = uuid.uuid4()
    mock_db.execute.side_effect = [db_result(scalar=make_user())]   # get_current_user

    r = await client.get(
        f"/v1/orgs/{other_org}/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 403


async def test_list_projects_returns_projects(db_client, admin_token):
    client, mock_db = db_client
    proj = make_project()
    mock_db.execute.side_effect = [
        db_result(scalar=make_user()),
        db_result(rows=[proj]),
    ]

    r = await client.get(
        f"/v1/orgs/{ORG_ID}/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "Acme Pilot"


# ---------------------------------------------------------------------------
# DELETE /v1/orgs/{org_id}/projects/{project_id}
# ---------------------------------------------------------------------------

async def test_delete_project_not_found_404(db_client, admin_token):
    import uuid
    client, mock_db = db_client
    mock_db.execute.side_effect = [
        db_result(scalar=make_user()),    # get_current_user
        db_result(scalar=None),           # project not found
    ]

    r = await client.delete(
        f"/v1/orgs/{ORG_ID}/projects/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404


async def test_delete_project_wrong_org_403(db_client, admin_token):
    import uuid
    client, mock_db = db_client
    mock_db.execute.side_effect = [db_result(scalar=make_user())]

    r = await client.delete(
        f"/v1/orgs/{uuid.uuid4()}/projects/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 403
