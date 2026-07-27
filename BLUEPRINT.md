# TrueFoundry-like Platform — Implementation Blueprint

> Based on TrueFoundry's architecture (screenshot: `Screenshot 2026-07-27 203241.png`) and website analysis.  
> Architecture pillars: **Discover & Govern → AI Gateway → Models / MCP Servers / Agents → Deploy & Scale → Observe**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Your AI Application                            │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│                            AI GATEWAY                                   │
│  Routing │ Guardrails │ Access Control │ Budget Controls │ Rate Limiting│
│  Load Balancing │ Fallback │ Prompt Management │ Analytics │ Governance │
└───────┬──────────────────────────┬──────────────────────────────────────┘
        │                          │                         │
┌───────▼───────┐  ┌───────────────▼──────┐  ┌─────────────▼─────────────┐
│    MODELS     │  │    MCP SERVERS       │  │        AGENTS             │
│  Commercial   │  │  Slack, Jira,        │  │  LangGraph, CrewAI,       │
│  Open Source  │  │  GitHub, Gmail       │  │  AutoGen, Custom          │
│  Finetuned    │  └──────────────────────┘  └───────────────────────────┘
└───────────────┘
        │                          │                         │
        └──────────────────────────▼─────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│                    DEPLOY & SCALE (Kubernetes-native)                   │
│         AWS │ Azure │ GCP │ On-Prem │ Air Gapped │ OpenShift           │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│                              OBSERVE                                    │
│        OpenTelemetry │ Grafana │ Prometheus │ Datadog │ GPU Metrics     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Decisions

| Layer | Recommended Technology |
|---|---|
| API server | FastAPI (Python) + gRPC for internal services |
| Gateway proxy | Envoy Proxy or custom FastAPI middleware |
| Orchestration | Kubernetes + Helm charts |
| Model serving | vLLM (GPU), Ollama (local), TGI (HuggingFace) |
| Agent runtime | LangGraph, CrewAI, AutoGen (pluggable) |
| MCP protocol | Official MCP SDK (Python/TypeScript) |
| Database | PostgreSQL (metadata), Redis (cache/rate-limit), ClickHouse (analytics) |
| Auth | Keycloak (OIDC/RBAC) or Auth0 |
| Observability | OpenTelemetry collector → Grafana + Prometheus + Tempo |
| Message queue | Redis Streams or Kafka (async agent tasks) |
| Frontend | Next.js + Tailwind (control plane UI) |
| IaC | Terraform + Helm (multi-cloud) |

---

## Phase 1 — Foundation & Core API Layer (Weeks 1–4)

### Goal
Stand up the skeleton: auth, multi-tenancy, project model, REST API.

### Steps

**1.1 Repository structure**
```
platform/
├── gateway/          # AI Gateway service
├── model-registry/   # Model catalog & serving
├── mcp-gateway/      # MCP server registry & proxy
├── agent-runtime/    # Agent deployment & execution
├── observer/         # Telemetry collection & storage
├── control-plane/    # Frontend dashboard (Next.js)
├── infra/            # Terraform modules per cloud
└── sdk/              # Python SDK for developers
```

**1.2 Data model (PostgreSQL)**
```sql
-- Core entities
organizations (id, name, slug, created_at)
projects      (id, org_id, name, settings_json)
users         (id, org_id, email, role)         -- roles: admin, member, viewer
api_keys      (id, user_id, hashed_key, scopes, budget_usd, expires_at)
```

**1.3 Auth service**
- Integrate Keycloak for OIDC; issue short-lived JWTs
- Scope system: `models:read`, `models:deploy`, `gateway:write`, `billing:read`
- API key hashing: SHA-256, never store plaintext

**1.4 REST API skeleton (FastAPI)**
```
POST   /v1/auth/token
GET    /v1/orgs/{org}/projects
POST   /v1/orgs/{org}/projects
GET    /v1/health
```

**Deliverable:** Auth working, projects CRUD, API key issuance.

---

## Phase 2 — AI Gateway (Weeks 5–10)

The central reverse-proxy that every AI request flows through. This is the most critical component.

### 2.1 Request Router
- Accepts OpenAI-compatible `/v1/chat/completions` endpoint (drop-in replacement)
- Routing rules stored in PostgreSQL; hot-reloaded without restart
- Routing strategies:
  - **Model alias**: `gpt-4` → route to Azure OpenAI or local vLLM instance
  - **Cost-based**: cheapest provider that meets latency SLA
  - **A/B split**: percentage traffic to two models
  - **Geo-routing**: EU requests → EU-hosted models only

```python
# gateway/router.py  (simplified)
class RouteSelector:
    def select(self, request: GatewayRequest, rules: list[RouteRule]) -> Endpoint:
        for rule in sorted(rules, key=lambda r: r.priority):
            if rule.matches(request):
                return rule.resolve_endpoint(strategy=rule.strategy)
        return self.default_endpoint
```

### 2.2 Rate Limiter
- Per (api_key, model) token-bucket in Redis
- Limits: requests/min, tokens/min, tokens/day
- Returns `429` with `Retry-After` header on breach

```python
# Redis key: ratelimit:{api_key}:{model}:rpm
# Use TOKEN BUCKET algorithm with MULTI/EXEC
```

### 2.3 Budget Controls
- Track spend in real time: `(input_tokens × input_price) + (output_tokens × output_price)`
- Configurable hard-stop threshold per API key / project / org
- Budget table in ClickHouse for fast aggregation:
```sql
budget_events (ts, org_id, project_id, api_key_id, model, input_tokens, output_tokens, cost_usd)
```

### 2.4 Load Balancer & Fallback
- Maintain a health-scored pool of endpoints per model alias
- Health check: `/health` ping every 10 s; drop endpoint on 3 consecutive failures
- Fallback chain: `[primary_model, fallback_model_1, fallback_model_2]`
- Circuit breaker: open after 5 failures in 30 s window

### 2.5 Guardrails
- **Input guardrails**: PII detection (Presidio), prompt injection detection, topic restriction
- **Output guardrails**: toxicity filter (use a small classifier model), regex deny-list, JSON schema validation
- Guardrail plugins implement a simple interface:
```python
class Guardrail(Protocol):
    async def check(self, text: str, context: RequestContext) -> GuardrailResult: ...
```

### 2.6 Prompt Management
- Store prompt templates with version numbers in PostgreSQL
- Variables interpolated at request time: `{{user_name}}`, `{{context}}`
- A/B test different prompt versions; track metrics per version
- API: `GET /v1/prompts/{slug}?version=3`

### 2.7 Analytics
- Every request writes a span to OpenTelemetry collector (async, non-blocking)
- Dashboard metrics: latency p50/p95/p99, token usage, error rate, cost per model
- Stored in ClickHouse; queried by control plane UI

### 2.8 Governance & Audit Log
- Immutable append-only log: every gateway request → `audit_log` table
- Fields: timestamp, user, api_key, model, input_hash (not plaintext), output_hash, latency, cost
- Export to S3 / GCS for compliance (HIPAA, SOC2)

**Deliverable:** OpenAI-compatible gateway with all 10 capabilities from the architecture diagram.

---

## Phase 3 — Model Registry & Serving (Weeks 8–14)

### 3.1 Model Catalog
Database of every available model endpoint:
```sql
models (
  id, slug, display_name, provider,   -- provider: openai | anthropic | huggingface | custom
  endpoint_url, auth_type,            -- auth_type: bearer | aws_sigv4 | none
  input_price_per_1k, output_price_per_1k,
  context_window, capabilities_json,  -- {"vision": true, "function_calling": true}
  deployment_id                       -- FK to deployed infra if self-hosted
)
```

### 3.2 Commercial Model Connectors
Adapter pattern — one adapter per provider, all sharing the same interface:
```python
class ModelAdapter(Protocol):
    async def complete(self, request: ChatRequest) -> ChatResponse: ...
    async def stream(self, request: ChatRequest) -> AsyncIterator[ChatChunk]: ...
```
Implement adapters for: OpenAI, Anthropic, Azure OpenAI, Google Vertex, Mistral, Cohere.

### 3.3 Open-Source Model Serving (vLLM)
- Deploy vLLM as a Kubernetes Deployment with GPU node selector
- Helm chart parameterized by `model_id`, `tensor_parallel_size`, `gpu_memory_fraction`
- Auto-register the vLLM endpoint in the model catalog on startup
- Support fractional GPU (MIG partitions on A100/H100) via `nvidia.com/mig-1g.5gb` resource

```yaml
# helm/vllm/values.yaml (key fields)
model: meta-llama/Llama-3.1-8B-Instruct
gpu:
  count: 1
  type: "nvidia.com/gpu"
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 4
  metric: queue_depth   # scale on pending requests
```

### 3.4 Fine-tuning Pipeline
- Job launcher: POST `/v1/finetune/jobs` → creates a Kubernetes Job
- Stages: data validation → tokenization → LoRA fine-tune → checkpoint eval → merge & push
- Checkpoints stored in S3/GCS; auto-register as a new model version on completion
- Framework: HuggingFace `trl` + `peft` (LoRA/QLoRA)

**Deliverable:** Unified model catalog, commercial + OSS connectors, fine-tune jobs.

---

## Phase 4 — MCP Server Gateway (Weeks 12–18)

MCP (Model Context Protocol) lets AI agents call external tools. This layer is a managed registry + proxy for MCP servers.

### 4.1 MCP Server Registry
```sql
mcp_servers (
  id, org_id, name, slug, description,
  transport,           -- stdio | sse | streamable_http
  endpoint_url,
  auth_config_json,    -- encrypted credentials
  capabilities_json,   -- list of tools exposed
  deployment_id
)
```

### 4.2 MCP Proxy
- Translates MCP tool calls from agents, injects auth credentials, forwards to server
- Enforces per-tool rate limiting and access control
- Logs every tool call for governance

### 4.3 Pre-built MCP Server Deployments
One-click deploy for common integrations:

| Integration | MCP Server | Auth method |
|---|---|---|
| Slack | `@modelcontextprotocol/server-slack` | OAuth2 |
| GitHub | `@modelcontextprotocol/server-github` | GitHub App |
| Gmail/GDrive | `@modelcontextprotocol/server-gdrive` | Google OAuth |
| Jira | Custom | API token |
| SQL DB | `mcp-server-sqlite` / postgres variant | Connection string |
| Web search | `@modelcontextprotocol/server-brave-search` | API key |

Each deployed as a Kubernetes Deployment, registered automatically in the registry.

### 4.4 Custom MCP Server SDK
Provide a Python library so users deploy their own tools:
```python
from platform_sdk.mcp import MCPServer, tool

server = MCPServer(name="my-company-api")

@tool(description="Fetch order status from our ERP")
async def get_order(order_id: str) -> dict:
    return await erp_client.get_order(order_id)

server.run()  # starts HTTP server, auto-registers with platform
```

**Deliverable:** MCP registry, proxy, 6 pre-built connectors, custom server SDK.

---

## Phase 5 — Agent Runtime (Weeks 16–22)

### 5.1 Agent Registry
```sql
agent_definitions (
  id, org_id, name, framework,    -- framework: langgraph | crewai | autogen | custom
  config_json,                    -- agent graph / crew definition
  model_alias,                    -- which model alias to use
  mcp_server_ids[],               -- tools the agent can access
  deployment_id
)
```

### 5.2 Agent Execution Engine
- Each agent run = a Kubernetes Job (short-lived) or a long-running Pod (persistent agent)
- Execution context injected as env vars: `GATEWAY_URL`, `API_KEY`, `MCP_PROXY_URL`
- State store: Redis (short-term memory) + PostgreSQL (long-term memory / conversation history)
- Streaming responses: SSE back to caller via gateway

### 5.3 Framework Adapters
Wrap each framework behind a standard lifecycle interface:
```python
class AgentRunner(Protocol):
    async def run(self, task: AgentTask) -> AsyncIterator[AgentEvent]: ...
    async def pause(self, run_id: str) -> None: ...
    async def resume(self, run_id: str, input: str) -> None: ...
```

Implement for: LangGraph, CrewAI, AutoGen, bare Python (custom).

### 5.4 Human-in-the-Loop
- Agents can emit `PAUSE_FOR_HUMAN` events
- Platform sends webhook / SSE to the calling application
- Resume endpoint: `POST /v1/agent-runs/{run_id}/resume`
- Timeout configurable; auto-cancels if no response

### 5.5 Agent Observability
Every agent step emits an OpenTelemetry span:
- `agent.task.start` / `agent.task.complete`
- `agent.llm.call` (model, tokens, latency)
- `agent.tool.call` (tool name, input_hash, latency, result_hash)
- Full trace visible in Grafana Tempo / Jaeger

**Deliverable:** Deploy & run agents across 4 frameworks, human-in-the-loop, full tracing.

---

## Phase 6 — Observability Stack (Weeks 10–16, parallel)

### 6.1 OpenTelemetry Pipeline
```
Services → OTel SDK → OTel Collector → 
                          ├─► Prometheus (metrics)
                          ├─► Tempo (traces)
                          ├─► Loki (logs)
                          └─► ClickHouse (analytics / cost)
```

### 6.2 Metrics to Collect

| Metric | Type | Labels |
|---|---|---|
| `gateway_requests_total` | Counter | model, status, org |
| `gateway_latency_seconds` | Histogram | model, route |
| `gateway_tokens_total` | Counter | model, type (input/output), org |
| `gateway_cost_usd_total` | Counter | model, org, project |
| `model_replica_count` | Gauge | model, namespace |
| `gpu_utilization_percent` | Gauge | node, gpu_index |
| `agent_run_duration_seconds` | Histogram | framework, status |
| `mcp_tool_calls_total` | Counter | server, tool, status |

### 6.3 Pre-built Grafana Dashboards
Provision via ConfigMap (Grafana dashboard-as-code):
- **Gateway Overview**: RPS, latency, error rate, cost
- **Model Performance**: per-model latency, token throughput, queue depth
- **Cost & Budget**: spend by org/project/model, budget utilization
- **Agent Runs**: success rate, step counts, tool usage
- **Infrastructure**: GPU utilization, node health, pod restarts

### 6.4 Alerting
Alertmanager rules:
- Budget > 80% consumed → Slack/email warning
- Budget > 100% → hard stop (gateway rejects requests)
- Model error rate > 5% for 5 min → PagerDuty
- GPU utilization > 90% for 10 min → scale-out trigger

**Deliverable:** Full observability; Grafana dashboards; alerting.

---

## Phase 7 — Multi-Cloud Deployment Engine (Weeks 18–26)

### 7.1 Kubernetes-Native Core
All platform components run on Kubernetes. The platform itself is deployed via Helm.

```
helm install truefoundry ./charts/platform \
  --set cloud=aws \
  --set region=us-east-1 \
  --set gpu.enabled=true
```

### 7.2 Terraform Modules (one per target)

```
infra/
├── modules/
│   ├── aws/        # EKS + RDS + ElastiCache + S3
│   ├── azure/      # AKS + Azure DB + Redis Cache + Blob
│   ├── gcp/        # GKE + Cloud SQL + Memorystore + GCS
│   ├── onprem/     # Kubernetes + local PostgreSQL + MinIO
│   └── airgapped/  # All above + private registry setup
└── environments/
    ├── dev/
    ├── staging/
    └── prod/
```

### 7.3 Air-Gapped Support
- All container images mirrored to private registry (Harbor)
- Model weights stored in internal S3-compatible store (MinIO)
- No external DNS/internet required at runtime
- Helm chart `airgapped: true` switches all image refs to private registry

### 7.4 GPU Node Pool Automation
- Terraform provisions GPU node pools (g5, A100, H100 variants)
- KEDA (Kubernetes Event-Driven Autoscaling) scales GPU pods on queue depth
- Node autoscaler terminates idle GPU nodes after configurable idle timeout
- MIG (Multi-Instance GPU) partitioning for A100/H100 via `nvidia-device-plugin`

### 7.5 Multi-Cluster Agent
For organizations with multiple Kubernetes clusters:
- Lightweight agent installed in each cluster (reads-only kubeconfig)
- Reports workload status to central control plane
- Control plane can target deployments to specific clusters via labels

**Deliverable:** One-command deploy to AWS/Azure/GCP/On-Prem; air-gapped mode; GPU autoscaling.

---

## Phase 8 — Control Plane UI (Weeks 20–28)

### 8.1 Tech Stack
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS + shadcn/ui components
- **State**: React Query (server state) + Zustand (UI state)
- **Charts**: Recharts or Tremor for dashboards
- **Auth**: NextAuth.js wired to Keycloak

### 8.2 Key UI Sections

| Section | Purpose |
|---|---|
| **Gateway** | Configure routes, guardrails, rate limits, view request logs |
| **Models** | Browse catalog, deploy new OSS model, launch fine-tune job |
| **MCP Servers** | One-click deploy integrations, manage credentials, view tool call logs |
| **Agents** | Upload agent definition, deploy, view run history and traces |
| **Observe** | Embedded Grafana panels, cost explorer, audit log viewer |
| **Settings** | RBAC (users/roles), billing, API keys, webhooks |

### 8.3 Developer SDK (Python)

```python
pip install truefoundry-sdk
```

```python
from truefoundry import TrueFoundry

tf = TrueFoundry(api_key="tfk_...")

# Deploy a model
tf.models.deploy(
    name="llama-3-8b",
    model_id="meta-llama/Llama-3.1-8B-Instruct",
    gpu_count=1
)

# Call through gateway
response = tf.gateway.chat(
    model="llama-3-8b",
    messages=[{"role": "user", "content": "Hello"}]
)

# Deploy an agent
tf.agents.deploy(
    name="support-agent",
    framework="langgraph",
    graph_path="./graph.py",
    tools=["github", "slack"]
)
```

---

## Phase 9 — Enterprise Features (Weeks 24–30)

### 9.1 RBAC
```
Organization
└── Projects
    └── Resources (models, agents, MCP servers)

Roles: org_admin, project_admin, developer, viewer
Permissions: granular per resource type + action
```

### 9.2 SSO / SAML
- SAML 2.0 and OIDC via Keycloak
- JIT (just-in-time) user provisioning
- Group → role mapping from IdP

### 9.3 Audit Log & Compliance
- All mutations logged to append-only table with actor, timestamp, diff
- Export to S3 with configurable retention (90d, 1y, 7y)
- Pre-built reports for SOC 2, HIPAA auditors

### 9.4 Data Residency
- Request/response bodies never stored by default (only hashes)
- Optional "store for debugging" mode with AES-256 encryption at rest
- KMS integration: AWS KMS, Azure Key Vault, GCP KMS, HashiCorp Vault

### 9.5 Network Policies
- All inter-service traffic via mTLS (Istio or Linkerd)
- Gateway enforces allowlist of egress IPs for each org
- Private Link / VPC Peering support for cloud deployments

---

## Phase 10 — Testing & Hardening (Ongoing)

### Test Strategy
```
Unit tests        → pytest, covers router logic, guardrails, budget calc
Integration tests → testcontainers (real PostgreSQL, Redis)
Load tests        → k6: 10k RPS gateway, measure p99 latency
Chaos tests       → chaos-mesh: kill model pods, verify fallback
Security tests    → OWASP ZAP scan, secret scanning (gitleaks)
E2E tests         → Playwright: UI flows for deploy → call → observe
```

### SLA Targets
| Component | Target |
|---|---|
| Gateway latency overhead | < 10 ms p99 added latency |
| Gateway availability | 99.9% |
| Control plane | 99.5% |
| Model serving (vLLM) | Autoscale within 2 min |

---

## Build Order Summary

| Phase | Weeks | Output |
|---|---|---|
| 1. Foundation | 1–4 | Auth, multi-tenancy, REST skeleton |
| 2. AI Gateway | 5–10 | Full gateway (all 10 capabilities) |
| 3. Model Registry | 8–14 | Catalog, connectors, vLLM, fine-tune |
| 4. MCP Gateway | 12–18 | MCP registry, proxy, 6 integrations |
| 5. Agent Runtime | 16–22 | Multi-framework agents, HITL |
| 6. Observability | 10–16 | OTel, Grafana, alerting |
| 7. Multi-Cloud Deploy | 18–26 | Terraform, air-gap, GPU autoscale |
| 8. Control Plane UI | 20–28 | Dashboard, SDK |
| 9. Enterprise | 24–30 | RBAC, SSO, compliance |
| 10. Hardening | Ongoing | Load tests, chaos, security |

**Estimated team:** 6–8 engineers (2 backend, 1 infra/DevOps, 1 ML infra, 1 frontend, 1 platform/SDK, 1 QA, 1 PM)  
**Estimated timeline to MVP (gateway + models + basic UI):** ~16 weeks  
**Estimated timeline to enterprise-ready v1:** ~30 weeks

---

## Critical Architectural Decisions

1. **OpenAI-compatible API**: Expose `/v1/chat/completions` — this makes every existing app work with zero code changes.
2. **Async-first gateway**: Use `asyncio` + `httpx` throughout; never block on model calls.
3. **Plugin interfaces**: Guardrails, model adapters, and agent runners are all protocols — swap implementations without touching gateway core.
4. **Immutable audit log**: Write to append-only table (PostgreSQL with row-level security, no DELETE permission for app user).
5. **Helm-first deployments**: Everything is a Helm chart. The control plane calls `helm upgrade --install` for every resource it deploys — users get standard K8s primitives.
6. **No vendor lock-in in the storage layer**: Abstract behind a `StorageBackend` interface (S3-compatible); works with AWS S3, GCS, Azure Blob, MinIO.
