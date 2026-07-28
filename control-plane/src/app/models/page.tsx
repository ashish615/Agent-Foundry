"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import AuthGuard from "@/components/AuthGuard";
import Modal from "@/components/Modal";
import { api, Model, ModelCreate } from "@/lib/api";
import { Plus, Trash2, BrainCircuit, Loader2, ToggleLeft, ToggleRight, ChevronDown, ChevronUp } from "lucide-react";

const PROVIDERS = ["openai", "anthropic", "google", "mistral", "cohere", "ollama", "vllm", "other"];
const CAPABILITIES = ["chat", "vision", "function_calling", "embeddings", "rerank", "code"];

const PROVIDER_COLORS: Record<string, string> = {
  openai: "bg-emerald-50 text-emerald-700",
  anthropic: "bg-orange-50 text-orange-700",
  google: "bg-blue-50 text-blue-700",
  mistral: "bg-purple-50 text-purple-700",
  cohere: "bg-cyan-50 text-cyan-700",
  ollama: "bg-gray-100 text-gray-700",
  vllm: "bg-indigo-50 text-indigo-700",
};

function ProviderBadge({ provider }: { provider: string }) {
  const cls = PROVIDER_COLORS[provider] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${cls}`}>
      {provider}
    </span>
  );
}

function CostCell({ val }: { val: number | null }) {
  if (val === null) return <span className="text-gray-400">—</span>;
  if (val === 0) return <span className="text-green-600 font-medium">Free</span>;
  return <span>${val.toFixed(2)}</span>;
}

function fmt(n: number | null) {
  if (n === null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`;
  return String(n);
}

export default function ModelsPage() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterProvider, setFilterProvider] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [createError, setCreateError] = useState("");
  const [confirmSlug, setConfirmSlug] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  // Form state
  const [form, setForm] = useState<ModelCreate>({
    slug: "", display_name: "", provider: "openai",
    endpoint_url: null, context_window: null, max_output_tokens: null,
    input_cost_per_1m: null, output_cost_per_1m: null,
    capabilities: ["chat"], is_active: true, meta_json: {},
  });

  async function load() {
    try {
      setModels(await api.listModels(filterProvider || undefined));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filterProvider]);

  function toggleCap(cap: string) {
    setForm((f) => ({
      ...f,
      capabilities: f.capabilities?.includes(cap)
        ? (f.capabilities ?? []).filter((c) => c !== cap)
        : [...(f.capabilities ?? []), cap],
    }));
  }

  function openModal() {
    setForm({ slug: "", display_name: "", provider: "openai", endpoint_url: null,
      context_window: null, max_output_tokens: null, input_cost_per_1m: null,
      output_cost_per_1m: null, capabilities: ["chat"], is_active: true, meta_json: {} });
    setCreateError("");
    setShowModal(true);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreateError("");
    setSaving(true);
    try {
      const m = await api.createModel(form);
      setModels((prev) => [...prev, m].sort((a, b) => a.provider.localeCompare(b.provider) || a.slug.localeCompare(b.slug)));
      setShowModal(false);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create model");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(slug: string, current: boolean) {
    try {
      const updated = await api.updateModel(slug, { is_active: !current });
      setModels((prev) => prev.map((m) => (m.slug === slug ? updated : m)));
    } catch {
      // ignore
    }
  }

  async function handleDelete(slug: string) {
    setDeleting(slug);
    try {
      await api.deleteModel(slug);
      setModels((prev) => prev.filter((m) => m.slug !== slug));
    } catch {
      // keep row
    } finally {
      setDeleting(null);
      setConfirmSlug(null);
    }
  }

  const displayed = filterProvider ? models.filter((m) => m.provider === filterProvider) : models;

  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Model Registry</h1>
              <p className="text-sm text-gray-500">{models.length} models · {models.filter((m) => m.is_active).length} active</p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={filterProvider}
                onChange={(e) => setFilterProvider(e.target.value)}
                className="rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
              >
                <option value="">All providers</option>
                {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
              <button
                onClick={openModal}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
              >
                <Plus className="h-4 w-4" /> Add Model
              </button>
            </div>
          </div>

          <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : displayed.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                <BrainCircuit className="mb-3 h-10 w-10" />
                <p className="text-sm">No models found. Add your first model.</p>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-gray-500">
                    <th className="px-5 py-3 font-medium">Model</th>
                    <th className="px-5 py-3 font-medium">Provider</th>
                    <th className="px-5 py-3 font-medium">Context</th>
                    <th className="px-5 py-3 font-medium">In / Out ($/1M)</th>
                    <th className="px-5 py-3 font-medium">Capabilities</th>
                    <th className="px-5 py-3 font-medium">Active</th>
                    <th className="px-5 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {displayed.map((m) => (
                    <>
                      <tr
                        key={m.slug}
                        className="border-b last:border-0 hover:bg-gray-50 cursor-pointer"
                        onClick={() => setExpanded(expanded === m.slug ? null : m.slug)}
                      >
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2">
                            {expanded === m.slug
                              ? <ChevronUp className="h-3.5 w-3.5 text-gray-400 shrink-0" />
                              : <ChevronDown className="h-3.5 w-3.5 text-gray-400 shrink-0" />}
                            <div>
                              <p className="font-medium">{m.display_name}</p>
                              <p className="font-mono text-xs text-gray-400">{m.slug}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-3"><ProviderBadge provider={m.provider} /></td>
                        <td className="px-5 py-3 text-gray-600">{fmt(m.context_window)}</td>
                        <td className="px-5 py-3 text-gray-600">
                          <CostCell val={m.input_cost_per_1m} />
                          {" / "}
                          <CostCell val={m.output_cost_per_1m} />
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex flex-wrap gap-1">
                            {m.capabilities.map((c) => (
                              <span key={c} className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">{c}</span>
                            ))}
                          </div>
                        </td>
                        <td className="px-5 py-3" onClick={(e) => e.stopPropagation()}>
                          <button onClick={() => toggleActive(m.slug, m.is_active)} title="Toggle active">
                            {m.is_active
                              ? <ToggleRight className="h-5 w-5 text-emerald-500" />
                              : <ToggleLeft className="h-5 w-5 text-gray-400" />}
                          </button>
                        </td>
                        <td className="px-5 py-3" onClick={(e) => e.stopPropagation()}>
                          {confirmSlug === m.slug ? (
                            <span className="flex items-center gap-2">
                              <span className="text-xs text-gray-500">Delete?</span>
                              <button
                                onClick={() => handleDelete(m.slug)}
                                disabled={deleting === m.slug}
                                className="text-xs font-medium text-red-600 hover:underline disabled:opacity-50"
                              >
                                {deleting === m.slug ? "…" : "Yes"}
                              </button>
                              <button onClick={() => setConfirmSlug(null)} className="text-xs text-gray-500 hover:underline">No</button>
                            </span>
                          ) : (
                            <button onClick={() => setConfirmSlug(m.slug)} className="text-red-400 hover:text-red-600">
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                      {expanded === m.slug && (
                        <tr key={`${m.slug}-detail`} className="bg-indigo-50/40 border-b">
                          <td colSpan={7} className="px-8 py-3 text-xs text-gray-600 space-y-1">
                            <div className="grid grid-cols-3 gap-4">
                              <div><span className="font-medium">Max output:</span> {fmt(m.max_output_tokens)} tokens</div>
                              <div><span className="font-medium">Endpoint:</span> {m.endpoint_url ?? "API (managed)"}</div>
                              <div><span className="font-medium">Added:</span> {new Date(m.created_at).toLocaleDateString()}</div>
                            </div>
                            {Object.keys(m.meta_json).length > 0 && (
                              <div><span className="font-medium">Meta:</span> {JSON.stringify(m.meta_json)}</div>
                            )}
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </main>
      </div>

      {showModal && (
        <Modal title="Add Model" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate} className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">Slug *</label>
                <input required value={form.slug}
                  onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value.toLowerCase().replace(/\s+/g, "-") }))}
                  placeholder="gpt-4o"
                  className="w-full rounded-lg border px-3 py-2 font-mono text-sm focus:border-indigo-500 focus:outline-none" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">Display name *</label>
                <input required value={form.display_name}
                  onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
                  placeholder="GPT-4o"
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">Provider *</label>
              <select value={form.provider}
                onChange={(e) => setForm((f) => ({ ...f, provider: e.target.value }))}
                className="w-full rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none">
                {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Endpoint URL <span className="font-normal text-gray-400">(for self-hosted)</span>
              </label>
              <input value={form.endpoint_url ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, endpoint_url: e.target.value || null }))}
                placeholder="http://localhost:11434"
                className="w-full rounded-lg border px-3 py-2 text-sm font-mono focus:border-indigo-500 focus:outline-none" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">Context window</label>
                <input type="number" min={0}
                  value={form.context_window ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, context_window: e.target.value ? +e.target.value : null }))}
                  placeholder="128000"
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">Max output tokens</label>
                <input type="number" min={0}
                  value={form.max_output_tokens ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, max_output_tokens: e.target.value ? +e.target.value : null }))}
                  placeholder="16384"
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">Input $/1M tokens</label>
                <input type="number" min={0} step="0.01"
                  value={form.input_cost_per_1m ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, input_cost_per_1m: e.target.value ? +e.target.value : null }))}
                  placeholder="5.00"
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">Output $/1M tokens</label>
                <input type="number" min={0} step="0.01"
                  value={form.output_cost_per_1m ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, output_cost_per_1m: e.target.value ? +e.target.value : null }))}
                  placeholder="15.00"
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none" />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-medium text-gray-700">Capabilities</label>
              <div className="flex flex-wrap gap-2">
                {CAPABILITIES.map((cap) => (
                  <button key={cap} type="button" onClick={() => toggleCap(cap)}
                    className={`rounded-md border px-2.5 py-1 text-xs transition-colors ${
                      form.capabilities?.includes(cap)
                        ? "border-indigo-500 bg-indigo-600 text-white"
                        : "border-gray-300 text-gray-600 hover:border-indigo-400"
                    }`}>
                    {cap}
                  </button>
                ))}
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_active ?? true}
                onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                className="rounded" />
              Active (available for routing)
            </label>

            {createError && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-600">{createError}</p>}

            <div className="flex justify-end gap-3 pt-1">
              <button type="button" onClick={() => setShowModal(false)}
                className="rounded-lg border px-4 py-2 text-sm hover:bg-gray-50">
                Cancel
              </button>
              <button type="submit" disabled={saving}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50">
                {saving && <Loader2 className="h-3 w-3 animate-spin" />}
                Add model
              </button>
            </div>
          </form>
        </Modal>
      )}
    </AuthGuard>
  );
}
