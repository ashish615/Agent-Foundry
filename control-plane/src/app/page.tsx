"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import AuthGuard from "@/components/AuthGuard";
import { useAuth } from "@/lib/auth";
import { api, Org, Project, ApiKey } from "@/lib/api";
import { Building2, Key, FolderKanban, CheckCircle2, AlertCircle } from "lucide-react";

function StatCard({
  label,
  value,
  icon: Icon,
  href,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-4 rounded-xl border bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-indigo-50">
        <Icon className="h-6 w-6 text-indigo-600" />
      </div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const { userId, orgId } = useAuth();
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    api.health().then((h) => setHealthy(h.status === "ok")).catch(() => setHealthy(false));
    api.listOrgs().then(setOrgs).catch(() => {});
    if (userId) api.listKeys(userId).then(setKeys).catch(() => {});
  }, [userId]);

  useEffect(() => {
    if (orgId) api.listProjects(orgId).then(setProjects).catch(() => {});
  }, [orgId]);

  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Dashboard</h1>
              <p className="text-sm text-gray-500">Overview of your Agent Foundry workspace</p>
            </div>
            <div className="flex items-center gap-2 text-sm">
              {healthy === null ? (
                <span className="text-gray-400">Checking gateway…</span>
              ) : healthy ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span className="text-green-600">Gateway online</span>
                </>
              ) : (
                <>
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span className="text-red-600">Gateway unreachable</span>
                </>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid gap-4 sm:grid-cols-3 mb-8">
            <StatCard label="Organizations" value={orgs.length} icon={Building2} href="/orgs" />
            <StatCard label="Projects" value={projects.length} icon={FolderKanban} href={orgId ? `/orgs/${orgId}/projects` : "/orgs"} />
            <StatCard label="API Keys" value={keys.length} icon={Key} href="/keys" />
          </div>

          {/* Recent orgs */}
          <div className="rounded-xl border bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold">Your Organizations</h2>
              <Link href="/orgs" className="text-sm text-indigo-600 hover:underline">View all</Link>
            </div>
            {orgs.length === 0 ? (
              <p className="text-sm text-gray-400">No organizations yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-2 font-medium">Name</th>
                    <th className="pb-2 font-medium">Slug</th>
                    <th className="pb-2 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {orgs.map((o) => (
                    <tr key={o.id} className="border-b last:border-0">
                      <td className="py-2 font-medium">{o.name}</td>
                      <td className="py-2 text-gray-500">{o.slug}</td>
                      <td className="py-2 text-gray-500">
                        {new Date(o.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
