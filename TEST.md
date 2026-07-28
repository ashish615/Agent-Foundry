# Test Suite — Agent Foundry

Complete reference for every test across all services. All tests run without a live database or external services — unit tests use mocked dependencies, protocol tests are pure Python.

---

## How to run

### Run one service at a time
```bash
cd <service-directory>
pip install -e ".[dev]"
pytest -v
```

### Run a single file or test
```bash
pytest tests/test_auth.py -v
pytest tests/test_auth.py::test_token_valid_key_returns_jwt -v
```

### Stop on first failure
```bash
pytest -x -v
```

---

## Services at a glance

| Service | Directory | Tests | How to run |
|---|---|---|---|
| Gateway | `gateway/` | 49 | `cd gateway && pytest -v` |
| Agent Runtime | `agent-runtime/` | 18 | `cd agent-runtime && pytest -v` |
| MCP Gateway | `mcp-gateway/` | 8 | `cd mcp-gateway && pytest -v` |
| Model Registry | `model-registry/` | 9 | `cd model-registry && pytest -v` |
| Observer | `observer/` | 8 | `cd observer && pytest -v` |
| Migrations | `migrations/` | 34 | `cd migrations && pytest -v` |
| SDK | `sdk/` | 21 | `cd sdk && pytest -v` |

---

---

## Gateway (`gateway/tests/`)

The most comprehensive suite — covers auth, CRUD endpoints, CORS, settings, and application metadata.

### `test_health.py` — 5 tests

| Test | What it checks |
|---|---|
| `test_health_status_200` | `GET /v1/health` returns HTTP 200 |
| `test_health_body` | Response body is exactly `{"status": "ok", "service": "gateway"}` |
| `test_health_content_type_json` | Content-Type header contains `application/json` |
| `test_health_unknown_path_returns_404` | A non-existent path returns 404 |
| `test_health_post_not_allowed` | `POST /v1/health` returns 405 Method Not Allowed |

---

### `test_app_meta.py` — 4 tests

| Test | What it checks |
|---|---|
| `test_app_title_contains_gateway` | The FastAPI app title includes the word "Gateway" |
| `test_app_version` | App version is `"0.1.0"` |
| `test_openapi_json_endpoint` | `GET /openapi.json` returns 200 with the correct title |
| `test_docs_endpoint_available` | Swagger UI at `/docs` returns 200 |

---

### `test_cors.py` — 5 tests

| Test | What it checks |
|---|---|
| `test_cors_header_present_for_cross_origin_request` | A request with an `Origin` header gets an `access-control-allow-origin` response header |
| `test_cors_wildcard_allows_any_origin` | Wildcard config allows any origin |
| `test_cors_preflight_returns_200` | `OPTIONS` preflight returns 200 |
| `test_cors_preflight_exposes_methods` | Preflight response includes `access-control-allow-methods` |
| `test_no_cors_header_without_origin` | Requests without an `Origin` header still return 200 (no CORS needed) |

---

### `test_settings.py` — 9 tests

| Test | What it checks |
|---|---|
| `test_default_database_url` | Default DB URL starts with `postgresql+asyncpg://` |
| `test_default_redis_url` | Default Redis URL starts with `redis://` |
| `test_default_cors_origins_wildcard` | Default CORS origins is `["*"]` |
| `test_default_otlp_endpoint` | Default OTLP endpoint is `http://localhost:4317` |
| `test_default_secret_key_not_empty` | Secret key is non-empty by default |
| `test_env_prefix_overrides_secret_key` | `GATEWAY_SECRET_KEY` env var overrides the setting |
| `test_env_prefix_overrides_redis_url` | `GATEWAY_REDIS_URL` env var overrides the setting |
| `test_env_prefix_overrides_database_url` | `GATEWAY_DATABASE_URL` env var overrides the setting |
| `test_cors_origins_can_be_list_of_domains` | `GATEWAY_CORS_ORIGINS` accepts a JSON array of domain strings |

---

### `test_auth.py` — 8 tests

Tests for `POST /v1/auth/token` and the auth middleware (JWT + API key Bearer token).

| Test | What it checks |
|---|---|
| `test_token_invalid_key_returns_401` | Posting a bad API key returns 401 Unauthorized |
| `test_token_valid_key_returns_jwt` | A valid API key returns a JWT with `token_type: bearer` and `expires_in: 3600` |
| `test_token_missing_body_returns_422` | Missing `api_key` field in the request body returns 422 Unprocessable Entity |
| `test_protected_route_no_auth_returns_401` | Calling a protected route with no `Authorization` header returns 401 |
| `test_protected_route_bad_jwt_returns_401` | A malformed Bearer token (not a valid JWT) returns 401 |
| `test_protected_route_valid_jwt_resolves_user` | A valid JWT in the `Authorization` header gives access to a protected route (200) |
| `test_member_token_cannot_create_org` | A token with only `completions` scope gets 403 when trying to create an org |
| `test_admin_token_can_create_org` | A token with `*` scope successfully creates an org and returns 201 |

---

### `test_orgs.py` — 10 tests

Tests for org listing and project CRUD endpoints.

| Test | What it checks |
|---|---|
| `test_list_orgs_no_auth_401` | `GET /v1/orgs` without auth returns 401 |
| `test_list_orgs_returns_users_own_org` | Authenticated user gets back their own org with correct `slug` |
| `test_list_orgs_empty_when_no_orgs` | Returns an empty list when the user's org has no match |
| `test_create_org_requires_org_admin_scope` | `POST /v1/orgs` with a `member`-role token returns 403 |
| `test_create_org_validates_body` | `POST /v1/orgs` without the required `slug` field returns 422 |
| `test_list_projects_no_auth_401` | `GET /v1/orgs/{id}/projects` without auth returns 401 |
| `test_list_projects_wrong_org_403` | Requesting projects for an org other than your own returns 403 |
| `test_list_projects_returns_projects` | Returns a list of projects for the user's own org |
| `test_delete_project_not_found_404` | Deleting a non-existent project returns 404 |
| `test_delete_project_wrong_org_403` | Deleting a project in another org returns 403 |

---

### `test_keys.py` — 8 tests

Tests for API key creation, listing, and deletion.

| Test | What it checks |
|---|---|
| `test_list_keys_no_auth_401` | `GET /v1/users/{id}/api-keys` without auth returns 401 |
| `test_list_keys_own_user_returns_keys` | Returns the user's own keys; response does NOT contain `plaintext_key` |
| `test_list_keys_other_user_non_admin_403` | A non-admin user cannot list another user's keys (403) |
| `test_create_key_requires_keys_write_scope` | Creating a key without `keys:write` scope returns 403 |
| `test_create_key_returns_plaintext_once` | Newly created key response includes `plaintext_key` starting with `af-`; scopes are preserved |
| `test_create_key_user_not_found_404` | Creating a key for a non-existent user returns 404 |
| `test_delete_key_not_found_404` | Deleting a non-existent key returns 404 |
| `test_delete_key_success_204` | Successfully deleting a key returns 204 No Content |

---

---

## Agent Runtime (`agent-runtime/tests/`)

### `test_health.py` — 5 tests

| Test | What it checks |
|---|---|
| `test_health_status_200` | `GET /v1/health` returns 200 |
| `test_health_body` | Response body is `{"status": "ok", "service": "agent-runtime"}` |
| `test_health_content_type_json` | Content-Type is `application/json` |
| `test_unknown_path_returns_404` | Unknown path returns 404 |
| `test_post_to_health_not_allowed` | `POST /v1/health` returns 405 |

---

### `test_app_meta.py` — 3 tests

| Test | What it checks |
|---|---|
| `test_app_title_contains_agent` | App title includes the word "Agent" |
| `test_app_version` | App version is `"0.1.0"` |
| `test_openapi_json_endpoint` | `/openapi.json` returns 200 with "Agent" in the title |

---

### `test_protocols.py` — 10 tests

Tests for `AgentTask`, `AgentEvent` data models and the `AgentRunner` Protocol. No HTTP — pure Python.

**AgentTask (4 tests)**

| Test | What it checks |
|---|---|
| `test_valid_task` | Creates a task with `run_id`, `agent_id`, `input` — all fields accessible |
| `test_context_defaults_to_empty_dict` | `context` field defaults to `{}` when not provided |
| `test_context_can_be_provided` | Custom context dict is stored and accessible |
| `test_missing_run_id_raises` | Omitting `run_id` raises `ValidationError` |
| `test_missing_agent_id_raises` | Omitting `agent_id` raises `ValidationError` |
| `test_missing_input_raises` | Omitting `input` raises `ValidationError` |
| `test_task_serializes_to_dict` | `model_dump()` returns the correct dict representation |

**AgentEvent (3 tests)**

| Test | What it checks |
|---|---|
| `test_valid_event` | Creates event with `run_id` and `type` |
| `test_payload_defaults_to_empty_dict` | `payload` defaults to `{}` |
| `test_payload_can_be_provided` | Custom payload (tool name, query) is stored correctly |
| `test_missing_run_id_raises` | Omitting `run_id` raises `ValidationError` |
| `test_missing_type_raises` | Omitting `type` raises `ValidationError` |
| `test_known_event_types_are_valid` | All expected event types (`step`, `tool_call`, `llm_response`, `complete`, `error`, `PAUSE_FOR_HUMAN`) are accepted |
| `test_event_serializes_to_dict` | `model_dump()` returns correct dict |

**AgentRunner Protocol (3 tests)**

| Test | What it checks |
|---|---|
| `test_protocol_has_run_method` | Protocol defines `run` |
| `test_protocol_has_pause_method` | Protocol defines `pause` |
| `test_protocol_has_resume_method` | Protocol defines `resume` |
| `test_concrete_class_satisfies_protocol` | A class with the right method signatures is structurally compatible with the Protocol |
| `test_concrete_runner_yields_events` | End-to-end: a runner accepts a task and yields a `step` event then a `complete` event |
| `test_runner_pause_is_awaitable` | `pause()` can be awaited without error |
| `test_runner_resume_is_awaitable` | `resume()` can be awaited without error |

---

---

## MCP Gateway (`mcp-gateway/tests/`)

### `test_health.py` — 5 tests

| Test | What it checks |
|---|---|
| `test_health_status_200` | `GET /v1/health` returns 200 |
| `test_health_body` | Response body is `{"status": "ok", "service": "mcp-gateway"}` |
| `test_health_content_type_json` | Content-Type is `application/json` |
| `test_unknown_path_returns_404` | Unknown path returns 404 |
| `test_post_to_health_not_allowed` | `POST /v1/health` returns 405 |

---

### `test_app_meta.py` — 3 tests

| Test | What it checks |
|---|---|
| `test_app_title_contains_mcp` | App title includes "MCP" |
| `test_app_version` | App version is `"0.1.0"` |
| `test_openapi_json_endpoint` | `/openapi.json` returns 200 with "MCP" in the title |

---

---

## Model Registry (`model-registry/tests/`)

### `test_health.py` — 5 tests

| Test | What it checks |
|---|---|
| `test_health_status_200` | `GET /v1/health` returns 200 |
| `test_health_body` | Response body is `{"status": "ok", "service": "model-registry"}` |
| `test_health_content_type_json` | Content-Type is `application/json` |
| `test_unknown_path_returns_404` | Unknown path returns 404 |
| `test_post_to_health_not_allowed` | `POST /v1/health` returns 405 |

---

### `test_app_meta.py` — 4 tests

| Test | What it checks |
|---|---|
| `test_app_title_contains_model_registry` | App title includes "Model Registry" |
| `test_app_version` | App version is `"0.1.0"` |
| `test_openapi_json_endpoint` | `/openapi.json` returns 200 with "Model Registry" in the title |
| `test_docs_endpoint_available` | Swagger UI at `/docs` returns 200 |

---

---

## Observer (`observer/tests/`)

### `test_health.py` — 5 tests

| Test | What it checks |
|---|---|
| `test_health_status_200` | `GET /v1/health` returns 200 |
| `test_health_body` | Response body is `{"status": "ok", "service": "observer"}` |
| `test_health_content_type_json` | Content-Type is `application/json` |
| `test_unknown_path_returns_404` | Unknown path returns 404 |
| `test_post_to_health_not_allowed` | `POST /v1/health` returns 405 |

---

### `test_app_meta.py` — 3 tests

| Test | What it checks |
|---|---|
| `test_app_title_contains_observer` | App title includes "Observer" |
| `test_app_version` | App version is `"0.1.0"` |
| `test_openapi_json_endpoint` | `/openapi.json` returns 200 with "Observer" in the title |

---

---

## Migrations (`migrations/tests/`)

No database required — all tests run against Python objects and a mock Alembic `op` recorder.

### `test_models.py` — 23 tests

Tests for SQLAlchemy ORM model definitions (`Organization`, `Project`, `User`, `ApiKey`).

**Table names (5 tests)**

| Test | What it checks |
|---|---|
| `test_organization_tablename` | `Organization.__tablename__` is `"organizations"` |
| `test_project_tablename` | `Project.__tablename__` is `"projects"` |
| `test_user_tablename` | `User.__tablename__` is `"users"` |
| `test_api_key_tablename` | `ApiKey.__tablename__` is `"api_keys"` |
| `test_all_four_tables_in_metadata` | All four tables are registered in `Base.metadata` |

**Organization columns & relationships (6 tests)**

| Test | What it checks |
|---|---|
| `test_id_is_primary_key` | `id` column is the primary key |
| `test_id_default_is_uuid4` | A new `Organization` instance gets a UUID `id` automatically |
| `test_slug_is_unique` | `slug` column has a unique constraint |
| `test_slug_not_nullable` | `slug` cannot be NULL |
| `test_name_not_nullable` | `name` cannot be NULL |
| `test_has_created_at` | `created_at` column exists |
| `test_has_projects_relationship` | `Organization` has a `.projects` relationship |
| `test_has_users_relationship` | `Organization` has a `.users` relationship |
| `test_projects_relationship_cascade_delete_orphan` | Deleting an org cascades to orphaned projects |
| `test_users_relationship_cascade_delete_orphan` | Deleting an org cascades to orphaned users |

**Project columns (4 tests)**

| Test | What it checks |
|---|---|
| `test_id_is_primary_key` | `id` is primary key |
| `test_org_id_has_fk_to_organizations` | `org_id` has a foreign key pointing to `organizations` |
| `test_org_id_not_nullable` | `org_id` cannot be NULL |
| `test_settings_json_not_nullable` | `settings_json` cannot be NULL |

**User columns (4 tests)**

| Test | What it checks |
|---|---|
| `test_email_is_unique` | `email` has a unique constraint |
| `test_email_not_nullable` | `email` cannot be NULL |
| `test_role_not_nullable` | `role` cannot be NULL |
| `test_api_keys_cascade_delete_orphan` | Deleting a user cascades to their API keys |

**ApiKey columns (5 tests)**

| Test | What it checks |
|---|---|
| `test_hashed_key_is_unique` | `hashed_key` has a unique constraint |
| `test_hashed_key_not_nullable` | `hashed_key` cannot be NULL |
| `test_budget_usd_is_nullable` | `budget_usd` may be NULL (no budget limit) |
| `test_expires_at_is_nullable` | `expires_at` may be NULL (never expires) |
| `test_last_used_at_is_nullable` | `last_used_at` may be NULL (never used) |

**Instance construction — no DB (12 tests)**

| Test | What it checks |
|---|---|
| `test_organization_instance` | Python-level construction sets `name`, `slug`, and auto-assigns UUID `id` |
| `test_project_instance` | `Project` stores `org_id`, `name`, and `settings_json` correctly |
| `test_user_instance_admin_role` | User with `role="admin"` stores the role |
| `test_user_instance_member_role` | User with `role="member"` stores the role |
| `test_user_instance_viewer_role` | User with `role="viewer"` stores the role |
| `test_api_key_with_scopes` | API key stores a list of scope strings |
| `test_api_key_budget_defaults_none` | `budget_usd` defaults to `None` |
| `test_api_key_expires_at_defaults_none` | `expires_at` defaults to `None` |
| `test_api_key_last_used_at_defaults_none` | `last_used_at` defaults to `None` |
| `test_api_key_with_budget` | `budget_usd` stores a `Decimal` value correctly |
| `test_two_organizations_have_different_ids` | Each new `Organization` instance gets a unique UUID |

---

### `test_migration_0001.py` — 11 tests

Tests the Alembic migration script structure without touching a real database. Uses a mock `op` recorder that captures DDL calls.

**Revision metadata (4 tests)**

| Test | What it checks |
|---|---|
| `test_revision_id` | `revision` is `"0001"` |
| `test_no_parent_revision` | `down_revision` is `None` (this is the first migration) |
| `test_no_branch_labels` | `branch_labels` is `None` |
| `test_no_depends_on` | `depends_on` is `None` |

**Callable guards (2 tests)**

| Test | What it checks |
|---|---|
| `test_upgrade_is_callable` | `upgrade` function exists and is callable |
| `test_downgrade_is_callable` | `downgrade` function exists and is callable |

**upgrade() operations (7 tests)**

| Test | What it checks |
|---|---|
| `test_creates_organizations_table` | `upgrade()` calls `create_table("organizations", ...)` |
| `test_creates_projects_table` | `upgrade()` calls `create_table("projects", ...)` |
| `test_creates_users_table` | `upgrade()` calls `create_table("users", ...)` |
| `test_creates_api_keys_table` | `upgrade()` calls `create_table("api_keys", ...)` |
| `test_creates_four_tables_total` | Exactly 4 tables are created — no more, no less |
| `test_creates_projects_org_id_index` | Index `idx_projects_org_id` is created |
| `test_creates_users_org_id_index` | Index `idx_users_org_id` is created |
| `test_creates_users_email_index` | Index `idx_users_email` is created |
| `test_creates_api_keys_user_id_index` | Index `idx_api_keys_user_id` is created |
| `test_creates_api_keys_hashed_key_index` | Index `idx_api_keys_hashed_key` is created |
| `test_creates_six_indexes_total` | Exactly 6 indexes are created |
| `test_executes_pgcrypto_extension` | `upgrade()` executes a SQL statement that enables `pgcrypto` |
| `test_executes_user_role_enum` | `upgrade()` executes a SQL statement that creates the `user_role` enum |

**downgrade() operations (5 tests)**

| Test | What it checks |
|---|---|
| `test_downgrade_drops_api_keys_before_users` | `api_keys` is dropped before `users` (FK order) |
| `test_downgrade_drops_users_before_organizations` | `users` is dropped before `organizations` (FK order) |
| `test_downgrade_drops_projects_before_organizations` | `projects` is dropped before `organizations` (FK order) |
| `test_downgrade_drops_all_four_tables` | All four tables are dropped in downgrade |
| `test_downgrade_drops_user_role_enum` | `user_role` enum is dropped in downgrade |

---

---

## SDK (`sdk/tests/`)

All SDK tests use `respx` to mock `httpx` — no live server needed.

### `test_client.py` — 21 tests

**Initialization (7 tests)**

| Test | What it checks |
|---|---|
| `test_sub_clients_are_created` | `AgentFoundry` creates `models`, `gateway`, `agents` sub-clients |
| `test_default_base_url` | Default base URL is `http://localhost:8000` |
| `test_custom_base_url` | Custom `base_url` is used when provided |
| `test_bearer_token_in_auth_header` | API key is sent as `Bearer <key>` in every request |
| `test_different_keys_produce_different_headers` | Two clients with different keys have different `authorization` headers |
| `test_async_context_manager_returns_self` | `async with AgentFoundry(...)` yields the client itself |
| `test_async_context_manager_closes_http_client` | Exiting the context manager closes the underlying `httpx` client |

**`_ModelsClient` (5 tests)**

| Test | What it checks |
|---|---|
| `test_list_returns_models` | `client.models.list()` returns the list of model dicts from the server |
| `test_list_returns_empty_list` | Returns `[]` when the server has no models |
| `test_list_raises_on_401_unauthorized` | Raises `HTTPStatusError` with status 401 on bad key |
| `test_list_raises_on_500_server_error` | Raises `HTTPStatusError` on server error |
| `test_list_sends_bearer_token` | The `authorization` header is sent with the correct Bearer token |

**`_GatewayClient` (7 tests)**

| Test | What it checks |
|---|---|
| `test_chat_returns_response` | `client.gateway.chat(...)` returns the full completion dict |
| `test_chat_sends_model_and_messages` | Request body contains the correct `model` and `messages` |
| `test_chat_forwards_extra_kwargs` | Extra kwargs (`temperature`, `max_tokens`) are included in the request body |
| `test_chat_raises_on_429_rate_limit` | Raises `HTTPStatusError` with status 429 on rate limit |
| `test_chat_raises_on_402_budget_exceeded` | Raises `HTTPStatusError` on budget exceeded (402) |
| `test_chat_with_empty_messages` | Handles an empty messages list without error |
| `test_chat_sends_bearer_token` | `authorization` header is correct on every chat request |

**`_AgentsClient` (4 tests)**

| Test | What it checks |
|---|---|
| `test_list_returns_agents` | `client.agents.list()` returns a list of agent dicts with `id`, `name`, `framework` |
| `test_list_returns_empty_list` | Returns `[]` when no agents exist |
| `test_list_raises_on_403_forbidden` | Raises `HTTPStatusError` with status 403 on insufficient permissions |
| `test_list_sends_bearer_token` | Bearer token is included in every agents request |

---

## Test design principles

**No live services required** — every test runs offline. Gateway and runtime tests mock the SQLAlchemy session with `AsyncMock`; SDK tests mock HTTP responses with `respx`; migration tests intercept Alembic `op` calls with a recorder object.

**Security invariants are tested explicitly** — `test_list_keys_own_user_returns_keys` asserts `"plaintext_key" not in data` to confirm the API never leaks the raw secret after creation.

**Scope enforcement has dedicated tests** — every mutation endpoint has at least one test proving it returns 403 when the caller lacks the required scope.

**FK ordering is verified** — `test_migration_0001.py` confirms `downgrade()` drops child tables before parent tables, preventing constraint violations on teardown.
