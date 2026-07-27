"""Tests for SQLAlchemy ORM models (no database required)."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import inspect as sa_inspect

from migrations.models import ApiKey, Base, Organization, Project, User


# ── Table names ────────────────────────────────────────────────────────────────

class TestTableNames:
    def test_organization_tablename(self):
        assert Organization.__tablename__ == "organizations"

    def test_project_tablename(self):
        assert Project.__tablename__ == "projects"

    def test_user_tablename(self):
        assert User.__tablename__ == "users"

    def test_api_key_tablename(self):
        assert ApiKey.__tablename__ == "api_keys"

    def test_all_four_tables_in_metadata(self):
        names = set(Base.metadata.tables.keys())
        assert {"organizations", "projects", "users", "api_keys"}.issubset(names)


# ── Organization columns ───────────────────────────────────────────────────────

class TestOrganizationColumns:
    def test_id_is_primary_key(self):
        col = Organization.__table__.c["id"]
        assert col.primary_key

    def test_id_default_is_uuid4(self):
        org = Organization(name="Test", slug="test")
        assert isinstance(org.id, uuid.UUID)

    def test_slug_is_unique(self):
        col = Organization.__table__.c["slug"]
        assert col.unique

    def test_slug_not_nullable(self):
        col = Organization.__table__.c["slug"]
        assert not col.nullable

    def test_name_not_nullable(self):
        col = Organization.__table__.c["name"]
        assert not col.nullable

    def test_has_created_at(self):
        assert "created_at" in Organization.__table__.c


# ── Organization relationships ─────────────────────────────────────────────────

class TestOrganizationRelationships:
    def test_has_projects_relationship(self):
        assert hasattr(Organization, "projects")

    def test_has_users_relationship(self):
        assert hasattr(Organization, "users")

    def test_projects_relationship_cascade_delete_orphan(self):
        rel = Organization.__mapper__.relationships["projects"]
        assert "delete-orphan" in rel.cascade

    def test_users_relationship_cascade_delete_orphan(self):
        rel = Organization.__mapper__.relationships["users"]
        assert "delete-orphan" in rel.cascade


# ── Project columns ─────────────────────────────────────────────────────────────

class TestProjectColumns:
    def test_id_is_primary_key(self):
        assert Project.__table__.c["id"].primary_key

    def test_org_id_has_fk_to_organizations(self):
        col = Project.__table__.c["org_id"]
        fks = list(col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].column.table.name == "organizations"

    def test_org_id_not_nullable(self):
        assert not Project.__table__.c["org_id"].nullable

    def test_name_not_nullable(self):
        assert not Project.__table__.c["name"].nullable

    def test_settings_json_not_nullable(self):
        assert not Project.__table__.c["settings_json"].nullable

    def test_has_organization_back_ref(self):
        assert hasattr(Project, "organization")


# ── User columns ───────────────────────────────────────────────────────────────

class TestUserColumns:
    def test_id_is_primary_key(self):
        assert User.__table__.c["id"].primary_key

    def test_email_is_unique(self):
        assert User.__table__.c["email"].unique

    def test_email_not_nullable(self):
        assert not User.__table__.c["email"].nullable

    def test_org_id_has_fk_to_organizations(self):
        col = User.__table__.c["org_id"]
        fks = list(col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].column.table.name == "organizations"

    def test_role_not_nullable(self):
        assert not User.__table__.c["role"].nullable

    def test_has_api_keys_relationship(self):
        assert hasattr(User, "api_keys")

    def test_api_keys_cascade_delete_orphan(self):
        rel = User.__mapper__.relationships["api_keys"]
        assert "delete-orphan" in rel.cascade


# ── ApiKey columns ─────────────────────────────────────────────────────────────

class TestApiKeyColumns:
    def test_id_is_primary_key(self):
        assert ApiKey.__table__.c["id"].primary_key

    def test_hashed_key_is_unique(self):
        assert ApiKey.__table__.c["hashed_key"].unique

    def test_hashed_key_not_nullable(self):
        assert not ApiKey.__table__.c["hashed_key"].nullable

    def test_user_id_has_fk_to_users(self):
        col = ApiKey.__table__.c["user_id"]
        fks = list(col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].column.table.name == "users"

    def test_budget_usd_is_nullable(self):
        assert ApiKey.__table__.c["budget_usd"].nullable

    def test_expires_at_is_nullable(self):
        assert ApiKey.__table__.c["expires_at"].nullable

    def test_last_used_at_is_nullable(self):
        assert ApiKey.__table__.c["last_used_at"].nullable

    def test_scopes_not_nullable(self):
        assert not ApiKey.__table__.c["scopes"].nullable

    def test_has_user_back_ref(self):
        assert hasattr(ApiKey, "user")


# ── Instance construction (Python-side, no DB) ─────────────────────────────────

class TestInstanceConstruction:
    def test_organization_instance(self):
        org = Organization(name="Acme Corp", slug="acme-corp")
        assert org.name == "Acme Corp"
        assert org.slug == "acme-corp"
        assert isinstance(org.id, uuid.UUID)

    def test_project_instance(self):
        org_id = uuid.uuid4()
        project = Project(org_id=org_id, name="My Project", settings_json={"env": "prod"})
        assert project.name == "My Project"
        assert project.org_id == org_id
        assert project.settings_json["env"] == "prod"

    def test_user_instance_admin_role(self):
        org_id = uuid.uuid4()
        user = User(org_id=org_id, email="alice@example.com", role="admin")
        assert user.email == "alice@example.com"
        assert user.role == "admin"

    def test_user_instance_member_role(self):
        org_id = uuid.uuid4()
        user = User(org_id=org_id, email="bob@example.com", role="member")
        assert user.role == "member"

    def test_user_instance_viewer_role(self):
        org_id = uuid.uuid4()
        user = User(org_id=org_id, email="carol@example.com", role="viewer")
        assert user.role == "viewer"

    def test_api_key_with_scopes(self):
        user_id = uuid.uuid4()
        key = ApiKey(user_id=user_id, hashed_key="abc123hex", scopes=["models:read", "gateway:write"])
        assert "models:read" in key.scopes
        assert "gateway:write" in key.scopes

    def test_api_key_budget_defaults_none(self):
        key = ApiKey(user_id=uuid.uuid4(), hashed_key="xyz", scopes=[])
        assert key.budget_usd is None

    def test_api_key_expires_at_defaults_none(self):
        key = ApiKey(user_id=uuid.uuid4(), hashed_key="xyz", scopes=[])
        assert key.expires_at is None

    def test_api_key_last_used_at_defaults_none(self):
        key = ApiKey(user_id=uuid.uuid4(), hashed_key="xyz", scopes=[])
        assert key.last_used_at is None

    def test_api_key_with_budget(self):
        key = ApiKey(user_id=uuid.uuid4(), hashed_key="k", scopes=[], budget_usd=Decimal("50.00"))
        assert key.budget_usd == Decimal("50.00")

    def test_two_organizations_have_different_ids(self):
        org1 = Organization(name="A", slug="a")
        org2 = Organization(name="B", slug="b")
        assert org1.id != org2.id
