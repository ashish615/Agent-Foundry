"""Seed script — inserts dummy data for local development and testing.

Usage (from repo root, with DATABASE_URL set):
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agentfoundry \
        python migrations/seed_data.py

Pass --reset to truncate all tables before inserting (order-safe, CASCADE respected).
"""

import argparse
import asyncio
import hashlib
import os
import secrets
import sys
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Allow running from repo root or from inside migrations/
sys.path.insert(0, os.path.dirname(__file__))
from models import ApiKey, Organization, Project, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_key(plaintext: str) -> str:
    """Return SHA-256 hex digest — the only thing we ever store."""
    return hashlib.sha256(plaintext.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _future(days: int) -> datetime:
    return _now() + timedelta(days=days)


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

ORGS = [
    {"name": "Acme Corp", "slug": "acme"},
    {"name": "Globex Inc", "slug": "globex"},
]

# (org_slug, email, role)
USERS = [
    ("acme", "alice@acme.example.com", "admin"),
    ("acme", "bob@acme.example.com", "member"),
    ("acme", "carol@acme.example.com", "viewer"),
    ("globex", "dave@globex.example.com", "admin"),
    ("globex", "eve@globex.example.com", "member"),
]

# (org_slug, name, settings)
PROJECTS = [
    ("acme", "Acme Gateway Pilot", {"model_default": "gpt-4o", "max_tokens": 4096}),
    ("acme", "Acme Internal Tools", {"model_default": "claude-sonnet-5", "max_tokens": 8192}),
    ("globex", "Globex Research Agent", {"model_default": "claude-opus-4-8", "max_tokens": 16384}),
]

# (user_email, scopes, budget_usd, expires_in_days)  — plaintext keys printed at end
API_KEYS_SPEC = [
    ("alice@acme.example.com",  ["*"],                     500.00,  365),
    ("bob@acme.example.com",    ["completions", "models"],  50.00,  90),
    ("carol@acme.example.com",  ["completions"],            10.00,  30),
    ("dave@globex.example.com", ["*"],                     200.00,  180),
    ("eve@globex.example.com",  ["completions"],            25.00,  60),
]


# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------

async def reset(session: AsyncSession) -> None:
    """Truncate all tables in dependency order."""
    await session.execute(text("TRUNCATE api_keys, users, projects, organizations RESTART IDENTITY CASCADE"))
    await session.commit()
    print("Tables truncated.")


async def seed(session: AsyncSession) -> None:
    org_by_slug: dict[str, Organization] = {}
    user_by_email: dict[str, User] = {}
    plaintext_keys: list[tuple[str, str]] = []  # (email, plaintext)

    # --- Organizations ---
    for spec in ORGS:
        org = Organization(id=uuid.uuid4(), name=spec["name"], slug=spec["slug"])
        session.add(org)
        org_by_slug[spec["slug"]] = org
    await session.flush()
    print(f"Inserted {len(ORGS)} organizations.")

    # --- Projects ---
    for org_slug, name, settings in PROJECTS:
        proj = Project(
            id=uuid.uuid4(),
            org_id=org_by_slug[org_slug].id,
            name=name,
            settings_json=settings,
        )
        session.add(proj)
    await session.flush()
    print(f"Inserted {len(PROJECTS)} projects.")

    # --- Users ---
    for org_slug, email, role in USERS:
        user = User(
            id=uuid.uuid4(),
            org_id=org_by_slug[org_slug].id,
            email=email,
            role=role,
        )
        session.add(user)
        user_by_email[email] = user
    await session.flush()
    print(f"Inserted {len(USERS)} users.")

    # --- API Keys ---
    for email, scopes, budget, expires_days in API_KEYS_SPEC:
        plaintext = f"af-{secrets.token_hex(24)}"
        key = ApiKey(
            id=uuid.uuid4(),
            user_id=user_by_email[email].id,
            hashed_key=_hash_key(plaintext),
            scopes=scopes,
            budget_usd=budget,
            expires_at=_future(expires_days),
        )
        session.add(key)
        plaintext_keys.append((email, plaintext))
    await session.flush()
    print(f"Inserted {len(API_KEYS_SPEC)} API keys.")

    await session.commit()

    # Print plaintext keys — only time they're visible; never stored
    print("\n--- Plaintext API keys (save these now, they will not be shown again) ---")
    for email, key in plaintext_keys:
        print(f"  {email:40s}  {key}")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main(reset_first: bool) -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("ERROR: DATABASE_URL environment variable is not set.")

    engine = create_async_engine(url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        if reset_first:
            await reset(session)
        await seed(session)

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed dummy data into Agent Foundry DB.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate all tables before inserting (safe for local dev, destructive in prod).",
    )
    args = parser.parse_args()
    asyncio.run(main(reset_first=args.reset))
