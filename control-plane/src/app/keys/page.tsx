"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import AuthGuard from "@/components/AuthGuard";
import Modal from "@/components/Modal";
import { useAuth } from "@/lib/auth";
import { api, ApiKey, ApiKeyCreated } from "@/lib/api";
import { Plus, Trash2, Copy, CheckCheck, Key, Loader2 } from "lucide-react";

const ALL_SCOPES = ["*", "completions", "org:admin", "keys:write"];

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <button onClick={copy} className="ml-2 inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs text-indigo-600 hover:bg-indigo-50">
      {copied ? <CheckCheck className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export default function KeysPage() {
  const { userId } = useAuth();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedScopes, setSelectedScopes] = useState<string[]>(["completions"]);
  const [budgetUsd, setBudgetUsd] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [saving, setSaving] = useState(false);
  const [createError, setCreateError] = useState("");
  const [newKey, setNewKey] = useState<ApiKeyCreated | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  async function load() {
    if (!userId) return;
    try {
      setKeys(await api.listKeys(userId));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [userId]);

  function toggleScope(scope: string) {
    setSelectedScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]
    );
  }

  function openModal() {
    setSelectedScopes(["completions"]);
    setBudgetUsd("");
    setExpiresAt("");
    setCreateError("");
    setNewKey(null);
    setShowModal(true);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!userId) return;
    setCreateError("");
    setSaving(true);
    try {
      const key = await api.createKey(
        userId,
        selectedScopes,
        budgetUsd ? parseFloat(budgetUsd) : null,
        expiresAt || null,
      );
      setNewKey(key);
      setKeys((prev) => [...prev, key]);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create key");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(keyId: string) {
    if (!userId) return;
    setDeleting(keyId);
    try {
      await api.deleteKey(userId, keyId);
      setKeys((prev) => prev.filter((k) => k.id !== keyId));
    } catch {
      // keep row on error
    } finally {
      setDeleting(null);
      setConfirmId(null);
    }
  }

  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">API Keys</h1>
              <p className="text-sm text-gray-500">Manage credentials for your account</p>
            </div>
            <button
              onClick={openModal}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
            >
              <Plus className="h-4 w-4" /> New API Key
            </button>
          </div>

          <div className="rounded-xl border bg-white shadow-sm">
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : keys.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                <Key className="mb-3 h-10 w-10" />
                <p className="text-sm">No API keys yet. Create one to get started.</p>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-gray-500">
                    <th className="px-5 py-3 font-medium">ID</th>
                    <th className="px-5 py-3 font-medium">Scopes</th>
                    <th className="px-5 py-3 font-medium">Budget</th>
                    <th className="px-5 py-3 font-medium">Expires</th>
                    <th className="px-5 py-3 font-medium">Last used</th>
                    <th className="px-5 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {keys.map((k) => (
                    <tr key={k.id} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="px-5 py-3 font-mono text-xs text-gray-500">{k.id.slice(0, 8)}…</td>
                      <td className="px-5 py-3">
                        <div className="flex flex-wrap gap-1">
                          {k.scopes.map((s) => (
                            <span key={s} className="rounded bg-indigo-50 px-1.5 py-0.5 text-xs text-indigo-700 font-mono">
                              {s}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-5 py-3 text-gray-500">
                        {k.budget_usd != null ? `$${k.budget_usd}` : "—"}
                      </td>
                      <td className="px-5 py-3 text-gray-500">
                        {k.expires_at ? new Date(k.expires_at).toLocaleDateString() : "Never"}
                      </td>
                      <td className="px-5 py-3 text-gray-500">
                        {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : "Never"}
                      </td>
                      <td className="px-5 py-3">
                        {confirmId === k.id ? (
                          <span className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">Revoke?</span>
                            <button
                              onClick={() => handleDelete(k.id)}
                              disabled={deleting === k.id}
                              className="text-xs font-medium text-red-600 hover:underline disabled:opacity-50"
                            >
                              {deleting === k.id ? "Revoking…" : "Yes"}
                            </button>
                            <button
                              onClick={() => setConfirmId(null)}
                              className="text-xs text-gray-500 hover:underline"
                            >
                              No
                            </button>
                          </span>
                        ) : (
                          <button
                            onClick={() => setConfirmId(k.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </main>
      </div>

      {showModal && (
        <Modal
          title={newKey ? "Key created — copy now" : "New API Key"}
          onClose={() => { setShowModal(false); setNewKey(null); }}
        >
          {newKey ? (
            <div className="space-y-4">
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                <p className="mb-2 text-xs font-semibold text-amber-800 uppercase tracking-wide">
                  Plaintext key — shown once
                </p>
                <div className="flex items-center justify-between rounded bg-white border px-3 py-2">
                  <code className="break-all text-xs text-gray-800">{newKey.plaintext_key}</code>
                  <CopyButton text={newKey.plaintext_key} />
                </div>
                <p className="mt-2 text-xs text-amber-700">
                  Store this now. It will not be shown again.
                </p>
              </div>
              <div className="text-sm text-gray-500 space-y-1">
                <p><span className="font-medium">Scopes:</span> {newKey.scopes.join(", ")}</p>
                {newKey.budget_usd && <p><span className="font-medium">Budget:</span> ${newKey.budget_usd}</p>}
              </div>
              <button
                onClick={() => { setShowModal(false); setNewKey(null); }}
                className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
              >
                Done
              </button>
            </div>
          ) : (
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium">Scopes</label>
                <div className="flex flex-wrap gap-2">
                  {ALL_SCOPES.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => toggleScope(s)}
                      className={`rounded-md border px-3 py-1 font-mono text-xs transition-colors ${
                        selectedScopes.includes(s)
                          ? "border-indigo-500 bg-indigo-600 text-white"
                          : "border-gray-300 text-gray-600 hover:border-indigo-400"
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">
                  Budget (USD) <span className="font-normal text-gray-400">optional</span>
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={budgetUsd}
                  onChange={(e) => setBudgetUsd(e.target.value)}
                  placeholder="10.00"
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">
                  Expires at <span className="font-normal text-gray-400">optional</span>
                </label>
                <input
                  type="datetime-local"
                  value={expiresAt}
                  onChange={(e) => setExpiresAt(e.target.value)}
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              {createError && (
                <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-600">{createError}</p>
              )}
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border px-4 py-2 text-sm hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving || selectedScopes.length === 0}
                  className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  {saving && <Loader2 className="h-3 w-3 animate-spin" />}
                  Create key
                </button>
              </div>
            </form>
          )}
        </Modal>
      )}
    </AuthGuard>
  );
}
