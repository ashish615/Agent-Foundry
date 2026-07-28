"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import {
  LayoutDashboard,
  Building2,
  BrainCircuit,
  Key,
  LogOut,
} from "lucide-react";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/orgs", label: "Organizations", icon: Building2 },
  { href: "/models", label: "Models", icon: BrainCircuit },
  { href: "/keys", label: "API Keys", icon: Key },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, orgId, userId } = useAuth();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-gray-200 bg-gray-900 text-white">
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-4 border-b border-gray-700">
        <span className="text-lg font-bold tracking-tight">Agent Foundry</span>
      </div>

      {/* Nav links */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-indigo-600 text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-700 p-3 space-y-2">
        {userId && (
          <p className="px-3 text-xs text-gray-500 truncate" title={userId}>
            {userId.slice(0, 8)}…
          </p>
        )}
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        >
          <LogOut className="h-4 w-4 shrink-0" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
