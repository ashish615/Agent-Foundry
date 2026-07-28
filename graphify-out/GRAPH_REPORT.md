# Graph Report - .  (2026-07-28)

## Corpus Check
- Corpus is ~10,235 words - fits in a single context window. You may not need a graph.

## Summary
- 444 nodes · 591 edges · 49 communities (28 shown, 21 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 55 edges (avg confidence: 0.54)
- Token cost: 36,000 input · 1,684 output

## Community Hubs (Navigation)
- Database Schema and ORM Models
- Agent Runtime Protocols
- SDK Client and Tests
- Migration Test Infrastructure
- Control Plane TypeScript Config
- Control Plane Dev Dependencies
- Gateway Service Core
- Architecture and Design Principles
- Control Plane Runtime Dependencies
- SDK HTTP Client Layer
- Migration Upgrade Tests
- Model Registry Service
- Agent Runtime Service
- MCP Gateway Service
- Observer Service
- Agent Runtime Health Tests
- Gateway CORS Tests
- Gateway Health Tests
- MCP Gateway Health Tests
- Model Registry Health Tests
- Observer Health Tests
- Alembic Migration Runner
- App Layout Component
- Homepage Component
- API Client Library
- Agent Runtime Package Init
- Next.js Configuration
- Migration Test Fixtures
- Model Registry Package Init
- Agent Runtime Package
- Gateway Package
- MCP Gateway Package
- Migrations Package
- Model Registry Package
- Observer Package
- SDK Package

## God Nodes (most connected - your core abstractions)
1. `AgentFoundry` - 33 edges
2. `TestInstanceConstruction` - 17 edges
3. `compilerOptions` - 16 edges
4. `AgentTask` - 15 edges
5. `Base` - 15 edges
6. `ApiKey` - 15 edges
7. `TestApiKeyColumns` - 15 edges
8. `README — Agent-Foundry Platform Implementation Blueprint` - 15 edges
9. `TestUpgradeOperations` - 14 edges
10. `AgentEvent` - 13 edges

## Surprising Connections (you probably didn't know these)
- `README — Agent-Foundry Platform Implementation Blueprint` --semantically_similar_to--> `CLAUDE.md — Project Guidance & Architecture Reference`  [INFERRED] [semantically similar]
  README.md → CLAUDE.md
- `Guardrail Protocol — Pluggable Input/Output Safety Interface` --semantically_similar_to--> `AgentRunner Protocol — Pluggable Agent Framework Interface`  [INFERRED] [semantically similar]
  README.md → CLAUDE.md
- `Gateway Service — OpenAI-Compatible AI Gateway (port 8000)` --implements--> `OpenAI-Compatible /v1/chat/completions API`  [EXTRACTED]
  CLAUDE.md → README.md
- `MCP Gateway Service — Tool Registry & Proxy (port 8002)` --implements--> `Model Context Protocol (MCP) — Agent Tool Integration Protocol`  [EXTRACTED]
  CLAUDE.md → README.md
- `Observer Service — OTel Pipeline & Prometheus Metrics (port 9090)` --implements--> `OpenTelemetry Pipeline — Metrics/Traces/Logs Collection`  [EXTRACTED]
  CLAUDE.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **All Python Services Share PostgreSQL via migrations/models.py ORM** — gateway_service, model_registry_service, mcp_gateway_service, agent_runtime_service, observer_service, migrations_models, postgres_service [EXTRACTED 1.00]
- **Pluggable Protocol Triad: Guardrails + ModelAdapters + AgentRunners** — guardrail_protocol, model_adapter_protocol, agent_runner_protocol [INFERRED 0.85]
- **Agent Runtime depends on Gateway + MCP Gateway + Redis + Postgres for full operation** — agent_runtime_service, gateway_service, mcp_gateway_service, redis_service, postgres_service [EXTRACTED 1.00]

## Communities (49 total, 21 thin omitted)

### Community 0 - "Database Schema and ORM Models"
Cohesion: 0.06
Nodes (14): DeclarativeBase, ApiKey, Base, Organization, Project, User, Tests for SQLAlchemy ORM models (no database required)., TestApiKeyColumns (+6 more)

### Community 1 - "Agent Runtime Protocols"
Cohesion: 0.09
Nodes (12): AgentEvent, AgentRunner, AgentTask, Protocol interfaces for agent framework adapters., Tests for AgentTask, AgentEvent, and AgentRunner protocol., A class with the right methods is structurally compatible., End-to-end: a concrete runner accepts a task and yields events., TestAgentEvent (+4 more)

### Community 2 - "SDK Client and Tests"
Cohesion: 0.13
Nodes (8): mock, AgentFoundry, Top-level SDK client., Tests for AgentFoundry SDK client., TestAgentFoundryInit, TestAgentsClient, TestGatewayClient, TestModelsClient

### Community 3 - "Migration Test Infrastructure"
Cohesion: 0.08
Nodes (12): _load_migration(), migration(), op_recorder(), _OpRecorder, fixture, Tests for the 0001_initial_schema Alembic migration (structure only, no DB neede, downgrade() must drop tables in the correct reverse-dependency order., Captures op.create_table and op.create_index calls. (+4 more)

### Community 4 - "Control Plane TypeScript Config"
Cohesion: 0.07
Nodes (26): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+18 more)

### Community 5 - "Control Plane Dev Dependencies"
Cohesion: 0.08
Nodes (25): autoprefixer, devDependencies, autoprefixer, eslint, eslint-config-next, postcss, @types/node, @types/react (+17 more)

### Community 6 - "Gateway Service Core"
Cohesion: 0.11
Nodes (17): BaseSettings, health(), get, Settings, client(), fixture, Tests for gateway FastAPI application metadata., Tests for gateway Settings (pydantic-settings). (+9 more)

### Community 7 - "Architecture and Design Principles"
Cohesion: 0.22
Nodes (24): AgentRunner Protocol — Pluggable Agent Framework Interface, Agent Runtime Service — Agent Execution Engine (port 8003), Async-First FastAPI Design Principle, CLAUDE.md — Project Guidance & Architecture Reference, Control Plane — Next.js Dashboard UI (port 3000), docker-compose.yml — Local Full-Stack Orchestration, Gateway Service — OpenAI-Compatible AI Gateway (port 8000), Guardrail Protocol — Pluggable Input/Output Safety Interface (+16 more)

### Community 8 - "Control Plane Runtime Dependencies"
Cohesion: 0.12
Nodes (17): dependencies, next, next-auth, react, react-dom, recharts, tailwindcss, @tanstack/react-query (+9 more)

### Community 9 - "SDK HTTP Client Layer"
Cohesion: 0.20
Nodes (5): AsyncClient, _AgentsClient, _GatewayClient, _ModelsClient, Agent Foundry Python SDK.

### Community 11 - "Model Registry Service"
Cohesion: 0.17
Nodes (5): health(), get, client(), fixture, Tests for model-registry FastAPI application metadata.

### Community 12 - "Agent Runtime Service"
Cohesion: 0.18
Nodes (5): health(), get, client(), fixture, Tests for agent-runtime FastAPI application metadata.

### Community 13 - "MCP Gateway Service"
Cohesion: 0.18
Nodes (5): health(), get, client(), fixture, Tests for mcp-gateway FastAPI application metadata.

### Community 14 - "Observer Service"
Cohesion: 0.18
Nodes (5): health(), get, client(), fixture, Tests for observer FastAPI application metadata.

### Community 21 - "Alembic Migration Runner"
Cohesion: 0.60
Nodes (3): do_run_migrations(), run_async_migrations(), run_migrations_online()

## Knowledge Gaps
- **56 isolated node(s):** `agent-foundry-agent-runtime`, `nextConfig`, `name`, `version`, `private` (+51 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentFoundry` connect `SDK Client and Tests` to `SDK HTTP Client Layer`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Why does `ApiKey` connect `Database Schema and ORM Models` to `Architecture and Design Principles`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `AgentFoundry` (e.g. with `TestAgentFoundryInit` and `TestAgentsClient`) actually correct?**
  _`AgentFoundry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TestInstanceConstruction` (e.g. with `ApiKey` and `Base`) actually correct?**
  _`TestInstanceConstruction` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AgentTask` (e.g. with `TestAgentEvent` and `TestAgentRunnerProtocol`) actually correct?**
  _`AgentTask` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `agent-foundry-agent-runtime`, `nextConfig`, `name` to the rest of the system?**
  _56 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Database Schema and ORM Models` be split into smaller, more focused modules?**
  _Cohesion score 0.057859703020993344 - nodes in this community are weakly interconnected._