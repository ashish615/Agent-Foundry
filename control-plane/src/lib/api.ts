const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  getProjects: (orgSlug: string) => apiFetch<{ id: string; name: string }[]>(`/v1/orgs/${orgSlug}/projects`),
  getModels: () => apiFetch<{ slug: string; display_name: string; provider: string }[]>("/v1/models"),
  getAgents: () => apiFetch<{ id: string; name: string; framework: string }[]>("/v1/agents"),
};
