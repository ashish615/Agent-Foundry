"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import AuthGuard from "@/components/AuthGuard";
import Modal from "@/components/Modal";
import { api, Project } from "@/lib/api";
import { ChevronRight, FolderOpen, Plus, Trash2, Loader2 } from "lucide-react";

export default function ProjectsPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  async function load() {
    try {
      setProjects(await api.listProjects(orgId));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [orgId]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const proj = await api.createProject(orgId, name.trim());
      setProjects((prev) => [...prev, proj]);
      setShowModal(false);
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(projectId: string) {
    setDeleting(projectId);
    try {
      await api.deleteProject(orgId, projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
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
          {/* Breadcrumb */}
          <nav className="mb-5 flex items-center gap-1.5 text-sm text-gray-500">
            <Link href="/orgs" className="hover:text-gray-800">Organizations</Link>
            <ChevronRight className="h-4 w-4" />
            <span className="font-mono text-gray-700">{orgId.slice(0, 8)}…</span>
            <ChevronRight className="h-4 w-4" />
            <span className="text-gray-900">Projects</span>
          </nav>

          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Projects</h1>
              <p className="text-sm text-gray-500">All projects inside this organization</p>
            </div>
            <button
              onClick={() => { setName(""); setError(""); setShowModal(true); }}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
            >
              <Plus className="h-4 w-4" /> New Project
            </button>
          </div>

          <div className="rounded-xl border bg-white shadow-sm">
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : projects.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                <FolderOpen className="mb-3 h-10 w-10" />
                <p className="text-sm">No projects yet. Create your first one.</p>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-gray-500">
                    <th className="px-5 py-3 font-medium">Name</th>
                    <th className="px-5 py-3 font-medium">ID</th>
                    <th className="px-5 py-3 font-medium">Created</th>
                    <th className="px-5 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr key={p.id} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="px-5 py-3 font-medium">{p.name}</td>
                      <td className="px-5 py-3 font-mono text-gray-400 text-xs">{p.id.slice(0, 8)}…</td>
                      <td className="px-5 py-3 text-gray-500">
                        {new Date(p.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-5 py-3">
                        {confirmId === p.id ? (
                          <span className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">Delete?</span>
                            <button
                              onClick={() => handleDelete(p.id)}
                              disabled={deleting === p.id}
                              className="text-xs font-medium text-red-600 hover:underline disabled:opacity-50"
                            >
                              {deleting === p.id ? "Deleting…" : "Yes"}
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
                            onClick={() => setConfirmId(p.id)}
                            className="flex items-center gap-1 text-red-500 hover:text-red-700"
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
        <Modal title="New Project" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">Project name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Pilot Agent"
                required
                className="w-full rounded-lg border px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            {error && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
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
                disabled={saving}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {saving && <Loader2 className="h-3 w-3 animate-spin" />}
                Create
              </button>
            </div>
          </form>
        </Modal>
      )}
    </AuthGuard>
  );
}
