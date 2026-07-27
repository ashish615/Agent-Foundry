-- Migration 001: core multi-tenancy schema (Phase 1 — Foundation)
-- Apply with: psql $DATABASE_URL -f migrations/001_initial_schema.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()

-- ── Organizations ────────────────────────────────────────────────────────────

CREATE TABLE organizations (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name       TEXT        NOT NULL,
    slug       TEXT        NOT NULL UNIQUE,  -- URL-safe identifier, e.g. "acme-corp"
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Projects ─────────────────────────────────────────────────────────────────

CREATE TABLE projects (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id        UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name          TEXT        NOT NULL,
    settings_json JSONB       NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (org_id, name)
);

CREATE INDEX idx_projects_org_id ON projects(org_id);

-- ── Users ────────────────────────────────────────────────────────────────────

CREATE TYPE user_role AS ENUM ('admin', 'member', 'viewer');

CREATE TABLE users (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id     UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email      TEXT        NOT NULL UNIQUE,
    role       user_role   NOT NULL DEFAULT 'member',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_org_id ON users(org_id);
CREATE INDEX idx_users_email  ON users(email);

-- ── API Keys ─────────────────────────────────────────────────────────────────
-- hashed_key stores SHA-256(plaintext_key); plaintext is never persisted.
-- scopes is an array of permission strings, e.g. '{models:read,gateway:write}'.

CREATE TABLE api_keys (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hashed_key  TEXT        NOT NULL UNIQUE,  -- SHA-256 hex digest
    scopes      TEXT[]      NOT NULL DEFAULT '{}',
    budget_usd  NUMERIC(12,4),               -- NULL means unlimited
    expires_at  TIMESTAMPTZ,                 -- NULL means never
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_used_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_user_id    ON api_keys(user_id);
CREATE INDEX idx_api_keys_hashed_key ON api_keys(hashed_key);

COMMIT;
