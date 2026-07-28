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
from models import ApiKey, Model, Organization, Project, User


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

# slug, display_name, provider, endpoint_url, context_window, max_output_tokens,
# input_cost_per_1m, output_cost_per_1m, capabilities, is_active, meta_json
MODELS_SPEC = [
    # ── Chat / multimodal ──────────────────────────────────────────────────────
    ("gpt-4o",                  "GPT-4o",                    "openai",    None,                    128_000, 16_384, 5.00,  15.00, ["chat","vision","function_calling"],        True, {}),
    ("gpt-4o-mini",             "GPT-4o Mini",               "openai",    None,                    128_000, 16_384, 0.15,   0.60, ["chat","vision","function_calling"],        True, {}),
    ("claude-sonnet-5",         "Claude Sonnet 5",           "anthropic", None,                    200_000, 64_000, 3.00,  15.00, ["chat","vision","function_calling"],        True, {}),
    ("claude-opus-4-8",         "Claude Opus 4.8",           "anthropic", None,                    200_000, 32_000,15.00,  75.00, ["chat","vision","function_calling"],        True, {}),
    ("claude-haiku-4-5",        "Claude Haiku 4.5",          "anthropic", None,                    200_000, 16_000, 0.80,   4.00, ["chat","function_calling"],                 True, {}),
    ("gemini-2.0-flash",        "Gemini 2.0 Flash",          "google",    None,                  1_000_000,  8_192, 0.10,   0.40, ["chat","vision","function_calling"],        True, {}),
    ("mistral-large-2",         "Mistral Large 2",           "mistral",   None,                    131_072,   None, 3.00,   9.00, ["chat","function_calling"],                 True, {}),
    ("llama-3.3-70b",           "Llama 3.3 70B",             "ollama",    "http://localhost:11434",128_000,   None, 0.00,   0.00, ["chat","function_calling"],                 True, {"note": "self-hosted"}),
    # ── Embeddings ─────────────────────────────────────────────────────────────
    ("text-embedding-3-large",  "Text Embedding 3 Large",    "openai",    None,                      8_191,   None, 0.13,   0.00, ["embeddings"],                              True, {"dimensions": 3072}),
    ("text-embedding-3-small",  "Text Embedding 3 Small",    "openai",    None,                      8_191,   None, 0.02,   0.00, ["embeddings"],                              True, {"dimensions": 1536}),
    ("text-embedding-004",      "Text Embedding 004",        "google",    None,                      2_048,   None, 0.00,   0.00, ["embeddings"],                              True, {"dimensions": 768}),
    ("mistral-embed",           "Mistral Embed",             "mistral",   None,                      8_192,   None, 0.10,   0.00, ["embeddings"],                              True, {"dimensions": 1024}),
    ("nomic-embed-text",        "Nomic Embed Text",          "ollama",    "http://localhost:11434",   8_192,   None, 0.00,   0.00, ["embeddings"],                              True, {"note": "self-hosted", "dimensions": 768}),
    # ── Reranking ──────────────────────────────────────────────────────────────
    ("cohere-rerank-3.5",       "Cohere Rerank 3.5",         "cohere",    None,                       None,   None, 2.00,   0.00, ["rerank"],                                  True, {"note": "per 1k searches"}),
    ("bge-reranker-v2-m3",      "BGE Reranker v2-M3",        "ollama",    "http://localhost:11434",   None,   None, 0.00,   0.00, ["rerank"],                                  True, {"note": "self-hosted, cross-encoder"}),
    ("mixedbread-rerank-v2",    "Mixedbread Rerank v2",      "vllm",      "http://localhost:8080",    None,   None, 0.00,   0.00, ["rerank"],                                  True, {"note": "self-hosted"}),
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
    await session.execute(text("TRUNCATE api_keys, users, projects, organizations, models RESTART IDENTITY CASCADE"))
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

    # --- Models ---
    from decimal import Decimal
    for slug, display_name, provider, endpoint_url, ctx, max_out, in_cost, out_cost, caps, active, meta in MODELS_SPEC:
        m = Model(
            id=uuid.uuid4(),
            slug=slug,
            display_name=display_name,
            provider=provider,
            endpoint_url=endpoint_url,
            context_window=ctx,
            max_output_tokens=max_out,
            input_cost_per_1m=Decimal(str(in_cost)) if in_cost is not None else None,
            output_cost_per_1m=Decimal(str(out_cost)) if out_cost is not None else None,
            capabilities=caps,
            is_active=active,
            meta_json=meta,
        )
        session.add(m)
    await session.flush()
    print(f"Inserted {len(MODELS_SPEC)} models.")

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
