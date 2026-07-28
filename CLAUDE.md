# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local stack (all services + dependencies)
```bash
cp .env.example .env          # fill in secrets first
docker compose up             # starts postgres, redis, all 5 Python services, control-plane
docker compose up gateway     # start a single service
```

### Running a Python service directly
Each service lives in its own directory with a `src/` layout. Run from within the service directory:
```bash
cd gateway
pip install -e ".[dev]"
uvicorn gateway.main:app --reload --port 8000
```

| Directory | Module | Default port | Env prefix |
|---|---|---|---|
| `gateway/` | `gateway.main:app` | 8000 | `GATEWAY_` |
| `model-registry/` | `model_registry.main:app` | 8001 | `MODEL_REGISTRY_` |
| `mcp-gateway/` | `mcp_gateway.main:app` | 8002 | (none) |
| `agent-runtime/` | `agent_runtime.main:app` | 8003 | (none) |
| `observer/` | `observer.main:app` | — (Prometheus :9090) | (none) |

### Running tests
Tests are per-service. Run from the service directory:
```bash
cd gateway && pytest                                                        # all tests
cd gateway && pytest tests/test_auth.py                                     # one file
cd gateway && pytest tests/test_auth.py::test_admin_token_can_create_org   # single test
cd gateway && pytest -x -v                                                  # stop on first failure
```

For migration/model tests:
```bash
cd migrations && pip install -e ".[dev]" && pytest
```

All services share the same pytest config (`asyncio_mode = "auto"`, `pythonpath = ["src"]`).

### Control plane (Next.js 14 App Router)
```bash
cd control-plane
npm install
npm run dev     # http://localhost:3000
npm run build
npm run lint
```

The control plane talks to two backends:
- `NEXT_PUBLIC_API_URL` → gateway (default `http://localhost:8000`)
- `NEXT_PUBLIC_MODEL_REGISTRY_URL` → model-registry (default `http://localhost:8001`)

### Database
```bash
# Run migrations (from repo root):
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_foundry \
  alembic -c migrations/alembic.ini upgrade head

# Seed dummy data (prints plaintext API keys once — save them):
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_foundry \
  python migrations/seed_data.py --reset
```

---

## Architecture

### Request flow
```
Control Plane (Next.js :3000)
    ↓                    ↓
gateway (:8000)     model-registry (:8001)   ← control plane talks to both directly
    ↓         ↓
model-registry   mcp-gateway (:8002)         ← gateway resolves model endpoints / tool calls
    ↓
agent-runtime (:8003)                        ← long-running agent pods; calls gateway each LLM hop
    ↓
observer (OTel → Prometheus :9090)           ← every service emits spans/metrics here
```

### Python service pattern
Every service follows the same layout:
- `src/<pkg>/__init__.py` — adds `migrations/` to `sys.path` so `from models import Foo` works without PYTHONPATH tricks (see below)
- `src/<pkg>/main.py` — creates the FastAPI `app`, registers routers, lifespan disposes the engine, `GET /v1/health`
- `src/<pkg>/settings.py` — `pydantic-settings` `BaseSettings` with a service-specific `env_prefix`
- `src/<pkg>/db.py` — creates `async_engine`, `async_sessionmaker`, exposes `get_db()` async generator dependency
- `src/<pkg>/schemas.py` — Pydantic v2 request/response models with `ConfigDict(from_attributes=True)` for ORM compat
- `src/<pkg>/routers/` — one file per resource group; router registered in `main.py`
- `tests/conftest.py` — `client` fixture via `httpx.AsyncClient(transport=ASGITransport(app=app))`; `mock_db` via `AsyncMock` with `app.dependency_overrides[get_db]`

### Shared ORM / migrations/ sys.path pattern
`migrations/models.py` is the **single source of truth** for the database schema. Services import ORM classes directly:
```python
from models import ApiKey, Model, Organization, Project, User
```
This works because each service's `__init__.py` prepends `migrations/` to `sys.path` at package import time. In Docker, `PYTHONPATH=/migrations` achieves the same effect. **Never define SQLAlchemy models inside a service directory.**

### Migrations
Alembic revisions live in `migrations/versions/`. Current chain:
- `0001_initial_schema.py` — `organizations`, `projects`, `users`, `api_keys`, `user_role` enum
- `0002_models.py` — `models` table (slug, provider, capabilities, costs, is_active)

Migration filenames start with digits and **cannot be imported normally**. Test code loads them via `importlib.util.spec_from_file_location`. When adding a new migration, update `migrations/models.py` and the new revision together.

### Database schema summary
- `organizations` → `projects` (CASCADE)
- `organizations` → `users` (CASCADE) → `api_keys` (CASCADE)
- `models` — standalone; columns: `slug` (unique), `provider`, `capabilities` (TEXT[]), `input_cost_per_1m`, `output_cost_per_1m`, `is_active`, `context_window`, `endpoint_url`, `meta_json`
- `api_keys.hashed_key` — SHA-256 hex of the plaintext key; plaintext is **never stored**

### Gateway auth system (`gateway/src/gateway/auth.py`)
- Uses `PyJWT>=2.8.0` (not `python-jose`). Import as `import jwt`, catch `jwt.InvalidTokenError`.
- `POST /v1/auth/token` — accepts `{"api_key": "af-<hex>"}`, returns JWT. Token payload: `{sub, org_id, scopes, exp}`.
- `get_current_user` dependency — tries JWT decode first (no DB hit); falls back to SHA-256 API key lookup.
- `require_scope(*scopes)` factory — returns a FastAPI dependency; wildcard `"*"` grants all scopes.
- Scopes in use: `org:admin`, `keys:write`, `completions`, `*`.
- `SQLAlchemy session.add()` and `session.delete()` are **synchronous** — do not `await` them.

### Gateway test mock pattern
`gateway/tests/conftest.py` establishes the pattern all gateway tests follow:
```python
session.add = MagicMock()      # sync in SQLAlchemy
session.delete = MagicMock()   # sync in SQLAlchemy
# execute/commit/refresh are AsyncMock (auto from AsyncMock parent)
mock_db.execute.side_effect = [db_result(...)]  # use side_effect list, not return_value
mock_db.refresh.side_effect = refresh_side_effect()  # sets obj.id and obj.created_at
```
Use `side_effect=[...]` (not `return_value`) on `execute` to avoid Python 3.12 `AsyncMock` unawaited-coroutine warnings. The `filterwarnings` in `gateway/pyproject.toml` suppresses the one remaining library-internal case.

### Control plane (`control-plane/`)
Next.js 14 App Router, all pages are client components (`"use client"`). Stack: Tailwind CSS, Zustand (`src/lib/auth.ts`), Lucide icons.

Key files:
- `src/lib/api.ts` — typed API client for both gateway and model-registry; reads JWT from `localStorage`; auto-redirects to `/login` on 401
- `src/lib/auth.ts` — Zustand store; decodes JWT (base64) to extract `userId`, `orgId`, `scopes`; checks token expiry on load
- `src/components/AuthGuard.tsx` — wraps protected pages; redirects to `/login` if no valid token
- `src/components/Sidebar.tsx` — navigation; uses `useAuth()` for logout

Pages: `/login`, `/` (dashboard), `/orgs`, `/orgs/[orgId]/projects`, `/models`, `/keys`

### Model Registry (`model-registry/`)
Full CRUD service for the `models` table. Env prefix: `MODEL_REGISTRY_`. No auth middleware (internal service; control plane calls it directly). Endpoints under `/v1/models`: list (filterable by `provider`, `active_only`), get by slug, create, patch, delete.

### SDK
`sdk/src/agent_foundry/client.py` — `AgentFoundry` top-level client with three namespaced sub-clients (`models`, `gateway`, `agents`). Tests use `respx` to mock httpx without a live server.

### Infra
`infra/modules/{aws,azure,gcp,onprem,airgapped}/` — one Terraform module per target. `infra/environments/{dev,staging,prod}/main.tf` uses AWS by default; swap the `source` to retarget. The `airgapped` module wraps `onprem` with Harbor + MinIO.

### AgentRunner protocol
`agent-runtime/src/agent_runtime/protocols.py` defines the `AgentRunner` Protocol all framework adapters must implement (`run`, `pause`, `resume`). Implement the protocol; never modify the file.

---

## Key Constraints

- **Never store plaintext API keys.** Only `hashlib.sha256(key.encode()).hexdigest()` goes into `api_keys.hashed_key`. API keys are generated as `af-{secrets.token_hex(24)}`.
- **`migrations/models.py` is canonical.** Update the ORM class and the corresponding Alembic revision together.
- **All FastAPI services are async-first.** `httpx.AsyncClient`, `asyncpg`, async SQLAlchemy only — no blocking I/O in request handlers.
- **Migration filenames start with digits** (`0001_…`, `0002_…`) and cannot be imported with normal `import`. Use `importlib.util.spec_from_file_location` in tests.
- **`GATEWAY_` prefix is required** for all gateway env vars. Model-registry uses `MODEL_REGISTRY_`. Other services currently have no prefix — check `settings.py` per service.
- **`session.add()` / `session.delete()` are sync.** Never `await` them. Only `execute`, `commit`, `refresh`, `flush` are async in SQLAlchemy's async session.
