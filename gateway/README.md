# Gateway Service

Central reverse-proxy for all AI traffic. Handles authentication, routing, rate limiting, guardrails, and budget controls. All external AI requests enter the platform through this service.

- **Port:** 8000
- **Module:** `gateway.main:app`
- **OpenAPI docs:** `http://localhost:8000/docs`

---

## Running locally

```bash
cd gateway
pip install -e ".[dev]"
uvicorn gateway.main:app --reload --port 8000
```

Or via Docker Compose from the repo root:

```bash
docker compose up gateway
```

---

## Environment variables

All variables use the `GATEWAY_` prefix (enforced by `pydantic-settings`).

| Variable | Default | Description |
|---|---|---|
| `GATEWAY_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/agent_foundry` | Async PostgreSQL connection string |
| `GATEWAY_REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `GATEWAY_SECRET_KEY` | `change-me-in-production` | HMAC secret for JWT signing — **change in prod** |
| `GATEWAY_JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `GATEWAY_JWT_EXPIRE_MINUTES` | `60` | JWT lifetime in minutes |
| `GATEWAY_CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `GATEWAY_OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry collector endpoint |

---

## Authentication

Every protected endpoint accepts one of:

- **JWT** — `Authorization: Bearer <token>` — obtained from `POST /v1/auth/token`. Decoded in-memory; no DB hit.
- **API key** — `Authorization: Bearer af-<hex>` — SHA-256 hash is looked up in `api_keys` table.

Unauthenticated requests receive `401`. Insufficient scope receives `403`.

### Scopes

| Scope | Grants |
|---|---|
| `*` | Everything (wildcard) |
| `org:admin` | Create/delete orgs and projects |
| `keys:write` | Issue and revoke API keys |
| `completions` | Call AI completion endpoints (Phase 2) |

---

## API Reference

### Health

#### `GET /v1/health`

Liveness check. No authentication required.

**Response `200`**
```json
{ "status": "ok", "service": "gateway" }
```

---

### Auth

#### `POST /v1/auth/token`

Exchange a plaintext API key for a short-lived JWT. No authentication required.

**Request body**
```json
{ "api_key": "af-<hex>" }
```

**Response `200`**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errors**
| Code | Reason |
|---|---|
| `401` | API key not found |
| `422` | `api_key` field missing |

---

### Organizations

#### `GET /v1/orgs`

List the organization(s) the authenticated user belongs to.

**Auth:** any valid credential

**Response `200`**
```json
[
  {
    "id": "uuid",
    "name": "Acme Corp",
    "slug": "acme",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

#### `POST /v1/orgs`

Create a new organization.

**Auth:** scope `org:admin` (or `*`)

**Request body**
```json
{ "name": "New Org", "slug": "new-org" }
```

**Response `201`** — same shape as org object above.

**Errors**
| Code | Reason |
|---|---|
| `403` | Missing `org:admin` scope |
| `422` | Validation error |

---

#### `GET /v1/orgs/{org_id}/projects`

List all projects inside an organization.

**Auth:** any valid credential belonging to `org_id`

**Response `200`**
```json
[
  {
    "id": "uuid",
    "org_id": "uuid",
    "name": "Pilot Project",
    "settings_json": {},
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

**Errors**
| Code | Reason |
|---|---|
| `403` | Caller does not belong to this org |

---

#### `POST /v1/orgs/{org_id}/projects`

Create a project inside an organization.

**Auth:** scope `org:admin` and caller must belong to `org_id`

**Request body**
```json
{ "name": "My Project", "settings_json": {} }
```

**Response `201`** — same shape as project object above.

---

#### `DELETE /v1/orgs/{org_id}/projects/{project_id}`

Delete a project.

**Auth:** scope `org:admin` and caller must belong to `org_id`

**Response `204` No Content**

**Errors**
| Code | Reason |
|---|---|
| `403` | Missing scope or wrong org |
| `404` | Project not found |

---

### API Keys

#### `GET /v1/users/{user_id}/api-keys`

List all API keys for a user. Plaintext key is **never** returned here.

**Auth:** own user, or any user with role `admin`

**Response `200`**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "scopes": ["completions"],
    "budget_usd": null,
    "expires_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "last_used_at": null
  }
]
```

---

#### `POST /v1/users/{user_id}/api-keys`

Issue a new API key. The `plaintext_key` field is returned **exactly once** and never stored — copy it immediately.

**Auth:** scope `keys:write`; own user or admin

**Request body**
```json
{
  "scopes": ["completions"],
  "budget_usd": null,
  "expires_at": null
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "scopes": ["completions"],
  "budget_usd": null,
  "expires_at": null,
  "created_at": "2024-01-01T00:00:00Z",
  "last_used_at": null,
  "plaintext_key": "af-<48 hex chars>"
}
```

**Errors**
| Code | Reason |
|---|---|
| `403` | Missing `keys:write` scope or not own user |
| `404` | Target user not found |

---

#### `DELETE /v1/users/{user_id}/api-keys/{key_id}`

Revoke an API key immediately.

**Auth:** scope `keys:write`; own user or admin

**Response `204` No Content**

**Errors**
| Code | Reason |
|---|---|
| `403` | Missing scope |
| `404` | Key not found |

---

## Running tests

```bash
cd gateway
pytest                     # all 49 tests
pytest -x -v               # stop on first failure, verbose
pytest tests/test_auth.py  # single file
```

Tests use `httpx.AsyncClient` with `ASGITransport` (no live server or database needed). The DB session is replaced by an `AsyncMock` fixture via `app.dependency_overrides`.

---

## Project structure

```
gateway/
├── Dockerfile
├── pyproject.toml
├── src/
│   └── gateway/
│       ├── __init__.py      # adds migrations/ to sys.path for local dev
│       ├── main.py          # FastAPI app, middleware, router registration
│       ├── settings.py      # pydantic-settings (GATEWAY_ prefix)
│       ├── db.py            # async engine + get_db dependency
│       ├── auth.py          # JWT helpers, get_current_user, require_scope
│       ├── schemas.py       # Pydantic request/response models
│       └── routers/
│           ├── auth.py      # POST /v1/auth/token
│           ├── orgs.py      # /v1/orgs and /v1/orgs/{id}/projects
│           └── keys.py      # /v1/users/{id}/api-keys
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_orgs.py
    ├── test_keys.py
    ├── test_health.py
    └── test_settings.py
```

> **Security:** Plaintext API keys are never stored. Only the SHA-256 hex digest is written to `api_keys.hashed_key`. The ORM models live in `migrations/models.py` — never inside this service directory.
