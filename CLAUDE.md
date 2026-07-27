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
Replace `gateway` / `gateway.main:app` / `8000` per service:

| Directory | Module | Default port |
|---|---|---|
| `gateway/` | `gateway.main:app` | 8000 |
| `model-registry/` | `model_registry.main:app` | 8001 |
| `mcp-gateway/` | `mcp_gateway.main:app` | 8002 |
| `agent-runtime/` | `agent_runtime.main:app` | 8003 |
| `observer/` | `observer.main:app` | — (Prometheus scrape :9090) |

### Running tests
Tests are per-service. Run from the service directory:
```bash
cd gateway && pytest                          # all tests in that service
cd gateway && pytest tests/test_health.py    # one file
cd gateway && pytest tests/test_health.py::test_health_status_200   # single test
cd gateway && pytest -x -v                   # stop on first failure, verbose
```

For migration/model tests (run from `migrations/`):
```bash
cd migrations && pip install -e ".[dev]" && pytest
```

All services share the same pytest config pattern (`asyncio_mode = "auto"`, `pythonpath = ["src"]`).

### Control plane (Next.js)
```bash
cd control-plane
npm install
npm run dev     # http://localhost:3000
npm run build
npm run lint
```

### Database migrations
```bash
# From repo root, with DATABASE_URL set:
DATABASE_URL=postgresql+asyncpg://... alembic -c migrations/alembic.ini upgrade head
DATABASE_URL=postgresql+asyncpg://... alembic -c migrations/alembic.ini downgrade -1
```

## Architecture

### Request flow
```
SDK / Application
    ↓
gateway (port 8000)        ← all AI traffic enters here; OpenAI-compatible /v1/chat/completions
    ↓                ↓
model-registry      mcp-gateway     ← gateway calls these to resolve model endpoints or tool calls
    ↓
agent-runtime                        ← long-running agent pods; calls gateway for every LLM hop
    ↓
observer (OTel → Prometheus :9090)  ← every service emits spans/metrics here
```

### Python service pattern
Every Python service (`gateway`, `model-registry`, `mcp-gateway`, `agent-runtime`, `observer`) follows the same layout:
- `src/<pkg>/main.py` — creates the FastAPI `app`, registers routers, `GET /v1/health`
- `src/<pkg>/settings.py` — `pydantic-settings` `BaseSettings` subclass; env vars use the service's prefix (e.g. `GATEWAY_DATABASE_URL`)
- `tests/conftest.py` — shared `client` fixture using `httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")`

Settings are always loaded at module import via a module-level `settings = Settings()` call in `main.py`. Override any setting with its prefixed env var (e.g. `GATEWAY_SECRET_KEY=...`).

### Shared data model
`migrations/models.py` is the **single source of truth** for the database schema. All four services import ORM classes from here — never define SQLAlchemy models inside a service directory. The Alembic revision in `migrations/versions/0001_initial_schema.py` must stay in sync with `models.py`.

Core schema: `organizations → projects`, `organizations → users → api_keys`. The `user_role` Postgres enum (`admin`, `member`, `viewer`) is defined in the migration and mirrored by the ORM.

`api_keys.hashed_key` stores SHA-256 of the plaintext key. Plaintext is never persisted anywhere.

### Protocol interfaces
`agent-runtime/src/agent_runtime/protocols.py` defines the `AgentRunner` Protocol that every framework adapter (LangGraph, CrewAI, AutoGen, custom) must implement:
```python
class AgentRunner(Protocol):
    async def run(self, task: AgentTask) -> AsyncIterator[AgentEvent]: ...
    async def pause(self, run_id: str) -> None: ...
    async def resume(self, run_id: str, input: str) -> None: ...
```
When adding a new framework adapter, implement this protocol — do not modify `protocols.py`.

### SDK
`sdk/src/agent_foundry/client.py` — `AgentFoundry` is the top-level client. It holds an `httpx.AsyncClient` with the bearer token and exposes three namespaced sub-clients (`models`, `gateway`, `agents`). SDK tests use `respx` to mock httpx responses without a live server.

### Infra
`infra/modules/{aws,azure,gcp,onprem,airgapped}/` — one Terraform module per target. `infra/environments/{dev,staging,prod}/main.tf` call the AWS module by default; swap the `source` to target a different cloud. The `airgapped` module wraps `onprem` and adds Harbor + MinIO.

## Key Constraints

- **Never store plaintext API keys.** Only SHA-256 hex digests go into `api_keys.hashed_key`.
- **`migrations/models.py` is canonical.** Alembic revision and ORM must match; update both together.
- **All FastAPI services are async-first.** Use `httpx.AsyncClient`, `asyncpg`, async SQLAlchemy — no blocking I/O in request handlers.
- **The migration filename `0001_initial_schema.py` starts with a digit** and cannot be imported normally. Tests load it via `importlib.util.spec_from_file_location`.
- **`GATEWAY_` prefix** is required for all gateway environment variables (enforced by `pydantic-settings`). Other services use no prefix by default; check their `settings.py`.
