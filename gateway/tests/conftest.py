"""Shared test fixtures for the gateway service."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from gateway.auth import create_access_token
from gateway.db import get_db
from gateway.main import app

# ---------------------------------------------------------------------------
# Stable fixture IDs so tests are deterministic
# ---------------------------------------------------------------------------

ORG_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
OTHER_USER_ID = uuid.uuid4()
PROJECT_ID = uuid.uuid4()
KEY_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# Mock-model factories
# ---------------------------------------------------------------------------

def make_user(role: str = "admin", scopes: list[str] | None = None, user_id=None, org_id=None):
    u = MagicMock()
    u.id = user_id or USER_ID
    u.org_id = org_id or ORG_ID
    u.email = "alice@acme.example.com"
    u.role = role
    u.created_at = datetime.now(timezone.utc)
    return u


def make_api_key(scopes: list[str] | None = None, expired: bool = False):
    k = MagicMock()
    k.id = KEY_ID
    k.user_id = USER_ID
    k.hashed_key = "deadbeef"
    k.scopes = scopes if scopes is not None else ["*"]
    k.budget_usd = Decimal("500.0000")
    k.expires_at = (
        datetime.now(timezone.utc) - timedelta(days=1)
        if expired
        else datetime.now(timezone.utc) + timedelta(days=365)
    )
    k.created_at = datetime.now(timezone.utc)
    k.last_used_at = None
    return k


def make_org():
    o = MagicMock()
    o.id = ORG_ID
    o.name = "Acme Corp"
    o.slug = "acme"
    o.created_at = datetime.now(timezone.utc)
    return o


def make_project():
    p = MagicMock()
    p.id = PROJECT_ID
    p.org_id = ORG_ID
    p.name = "Acme Pilot"
    p.settings_json = {}
    p.created_at = datetime.now(timezone.utc)
    return p


def refresh_side_effect():
    """AsyncMock side_effect for db.refresh — stamps server-side defaults (id, created_at)."""
    async def _refresh(obj):
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)
        # last_used_at is nullable — keep as None if not explicitly set
        if not hasattr(obj, "last_used_at"):
            obj.last_used_at = None
    return _refresh


def db_result(scalar=None, rows: list | None = None):
    """Build a mock that mimics the object returned by ``await session.execute(...)``."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar
    _scalars = MagicMock()
    _scalars.all.return_value = rows if rows is not None else ([] if scalar is None else [scalar])
    result.scalars.return_value = _scalars
    return result


# ---------------------------------------------------------------------------
# Base client (no DB override — for routes that don't touch the DB)
# ---------------------------------------------------------------------------

@pytest.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# Client with mocked DB session
# ---------------------------------------------------------------------------

@pytest.fixture
async def mock_db():
    session = AsyncMock()
    # session.add() and session.delete() are synchronous in SQLAlchemy;
    # AsyncMock would make them return unawaited coroutines.
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


@pytest.fixture
async def db_client(mock_db):
    """Yields (client, mock_db). Routes see the mock session instead of a real DB."""
    async def _override():
        yield mock_db

    app.dependency_overrides[get_db] = _override
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c, mock_db
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# JWT token helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_token():
    return create_access_token(str(USER_ID), str(ORG_ID), ["*"])


@pytest.fixture
def member_token():
    return create_access_token(str(USER_ID), str(ORG_ID), ["completions"])
