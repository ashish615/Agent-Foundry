const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const MODEL_REGISTRY_URL = process.env.NEXT_PUBLIC_MODEL_REGISTRY_URL ?? "http://localhost:8001";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("gw_token");
}

async function apiFetch<T>(path: string, init?: RequestInit, baseUrl = BASE_URL): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${baseUrl}${path}`, { ...init, headers });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("gw_token");
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `API ${path} → ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface Org {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface Project {
  id: string;
  org_id: string;
  name: string;
  settings_json: Record<string, unknown>;
  created_at: string;
}

export interface ApiKey {
  id: string;
  user_id: string;
  scopes: string[];
  budget_usd: number | null;
  expires_at: string | null;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreated extends ApiKey {
  plaintext_key: string;
}

export interface Model {
  id: string;
  slug: string;
  display_name: string;
  provider: string;
  endpoint_url: string | null;
  context_window: number | null;
  max_output_tokens: number | null;
  input_cost_per_1m: number | null;
  output_cost_per_1m: number | null;
  capabilities: string[];
  is_active: boolean;
  meta_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ModelCreate {
  slug: string;
  display_name: string;
  provider: string;
  endpoint_url?: string | null;
  context_window?: number | null;
  max_output_tokens?: number | null;
  input_cost_per_1m?: number | null;
  output_cost_per_1m?: number | null;
  capabilities?: string[];
  is_active?: boolean;
  meta_json?: Record<string, unknown>;
}

// ── API client ─────────────────────────────────────────────────────────────
export const api = {
  health: () => apiFetch<{ status: string; service: string }>("/v1/health"),

  login: (api_key: string) =>
    apiFetch<TokenResponse>("/v1/auth/token", {
      method: "POST",
      body: JSON.stringify({ api_key }),
    }),

  listOrgs: () => apiFetch<Org[]>("/v1/orgs"),
  createOrg: (name: string, slug: string) =>
    apiFetch<Org>("/v1/orgs", {
      method: "POST",
      body: JSON.stringify({ name, slug }),
    }),

  listProjects: (orgId: string) =>
    apiFetch<Project[]>(`/v1/orgs/${orgId}/projects`),
  createProject: (orgId: string, name: string, settings_json: Record<string, unknown> = {}) =>
    apiFetch<Project>(`/v1/orgs/${orgId}/projects`, {
      method: "POST",
      body: JSON.stringify({ name, settings_json }),
    }),
  deleteProject: (orgId: string, projectId: string) =>
    apiFetch<void>(`/v1/orgs/${orgId}/projects/${projectId}`, { method: "DELETE" }),

  listKeys: (userId: string) => apiFetch<ApiKey[]>(`/v1/users/${userId}/api-keys`),
  createKey: (userId: string, scopes: string[], budget_usd?: number | null, expires_at?: string | null) =>
    apiFetch<ApiKeyCreated>(`/v1/users/${userId}/api-keys`, {
      method: "POST",
      body: JSON.stringify({ scopes, budget_usd: budget_usd ?? null, expires_at: expires_at ?? null }),
    }),
  deleteKey: (userId: string, keyId: string) =>
    apiFetch<void>(`/v1/users/${userId}/api-keys/${keyId}`, { method: "DELETE" }),

  // Model Registry (port 8001)
  listModels: (provider?: string, activeOnly?: boolean) => {
    const params = new URLSearchParams();
    if (provider) params.set("provider", provider);
    if (activeOnly) params.set("active_only", "true");
    const qs = params.toString() ? `?${params}` : "";
    return apiFetch<Model[]>(`/v1/models${qs}`, undefined, MODEL_REGISTRY_URL);
  },
  getModel: (slug: string) =>
    apiFetch<Model>(`/v1/models/${slug}`, undefined, MODEL_REGISTRY_URL),
  createModel: (body: ModelCreate) =>
    apiFetch<Model>("/v1/models", { method: "POST", body: JSON.stringify(body) }, MODEL_REGISTRY_URL),
  updateModel: (slug: string, patch: Partial<ModelCreate> & { is_active?: boolean }) =>
    apiFetch<Model>(`/v1/models/${slug}`, { method: "PATCH", body: JSON.stringify(patch) }, MODEL_REGISTRY_URL),
  deleteModel: (slug: string) =>
    apiFetch<void>(`/v1/models/${slug}`, { method: "DELETE" }, MODEL_REGISTRY_URL),
};
