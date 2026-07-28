# Migrations

Database schema management and seed data for Agent Foundry.

## Prerequisites

- PostgreSQL running and accessible
- `DATABASE_URL` environment variable set (async driver required)
- Python dependencies installed

```bash
cd migrations
pip install -e ".[dev]"
```

Set the connection string once so you don't repeat it in every command:

```bash
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_foundry
```

---

## 1. Create the schema

Run Alembic from the `migrations/` directory. This creates all tables, indexes, the `user_role` enum, and the `pgcrypto` extension.

```bash
cd migrations
alembic -c alembic.ini upgrade head
```

Expected output:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, Initial schema: organizations, projects, users, api_keys
```

Verify the tables exist:

```bash
psql $DATABASE_URL -c "\dt"
```

```
 Schema |     Name      | Type  |  Owner
--------+---------------+-------+----------
 public | alembic_version | table | postgres
 public | api_keys      | table | postgres
 public | organizations | table | postgres
 public | projects      | table | postgres
 public | users         | table | postgres
```

---

## 2. Add dummy data

The seed script inserts two organizations, three projects, five users, and five API keys. Run it from the repo root:

```bash
pip install psycopg2-binary --break-system-packages
pip install asyncpg --break-system-packages
cd ..   # repo root
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_foundry python migrations/seed_data.py```

Expected output:

```
Inserted 2 organizations.
Inserted 3 projects.
Inserted 5 users.
Inserted 5 API keys.

--- Plaintext API keys (save these now, they will not be shown again) ---
  alice@acme.example.com      af-<hex>
  bob@acme.example.com        af-<hex>
  carol@acme.example.com      af-<hex>
  dave@globex.example.com     af-<hex>
  eve@globex.example.com      af-<hex>

Done.
```

> The plaintext keys are printed once and never stored. Copy them now if you need them for local testing.

To wipe all rows and re-seed from scratch (safe for local dev only):

```bash
python migrations/seed_data.py --reset
```

---

## 3. Remove all data (keep tables)

Truncate every table in dependency order:

```bash
psql $DATABASE_URL -c "TRUNCATE api_keys, users, projects, organizations RESTART IDENTITY CASCADE;"
```

This removes all rows but leaves the schema intact so you can re-seed without re-running migrations.

---

## 4. Remove all tables (tear down schema)

Run the Alembic downgrade to revision `base`. This drops every table and the `user_role` enum in reverse dependency order.

```bash
cd migrations
alembic -c alembic.ini downgrade base
```

Expected output:

```
INFO  [alembic.runtime.migration] Running downgrade 0001 -> , Initial schema: organizations, projects, users, api_keys
```

Verify everything is gone:

```bash
psql $DATABASE_URL -c "\dt"
```

```
Did not find any relations.
```

---

## Schema overview

| Table | Key columns | Notes |
|---|---|---|
| `organizations` | `id`, `name`, `slug` | Root entity; owns projects and users |
| `projects` | `id`, `org_id`, `name`, `settings_json` | Scoped to one org |
| `users` | `id`, `org_id`, `email`, `role` | `role` is `admin \| member \| viewer` |
| `api_keys` | `id`, `user_id`, `hashed_key`, `scopes`, `budget_usd`, `expires_at` | Only SHA-256 digest stored; plaintext never persisted |

## Common commands reference

| Goal | Command |
|---|---|
| Apply all migrations | `alembic -c alembic.ini upgrade head` |
| Roll back one revision | `alembic -c alembic.ini downgrade -1` |
| Roll back everything | `alembic -c alembic.ini downgrade base` |
| Show current revision | `alembic -c alembic.ini current` |
| Show migration history | `alembic -c alembic.ini history` |
| Seed dummy data | `python migrations/seed_data.py` |
| Wipe rows and re-seed | `python migrations/seed_data.py --reset` |
| Truncate rows only | `psql $DATABASE_URL -c "TRUNCATE api_keys, users, projects, organizations RESTART IDENTITY CASCADE;"` |
