const sections = [
  { href: "/gateway", label: "Gateway", description: "Routes, guardrails, rate limits, request logs" },
  { href: "/models", label: "Models", description: "Browse catalog, deploy OSS models, fine-tune jobs" },
  { href: "/mcp-servers", label: "MCP Servers", description: "One-click integrations, credentials, tool call logs" },
  { href: "/agents", label: "Agents", description: "Deploy agents, view run history and traces" },
  { href: "/observe", label: "Observe", description: "Grafana panels, cost explorer, audit log" },
  { href: "/settings", label: "Settings", description: "RBAC, billing, API keys, webhooks" },
];

export default function HomePage() {
  return (
    <main className="min-h-screen p-8">
      <h1 className="text-3xl font-bold mb-2">Agent Foundry</h1>
      <p className="text-gray-500 mb-8">AI Gateway · Model Registry · MCP Servers · Agent Runtime</p>
      <nav className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sections.map((s) => (
          <a
            key={s.href}
            href={s.href}
            className="block rounded-lg border p-6 hover:bg-gray-50 transition-colors"
          >
            <h2 className="font-semibold text-lg mb-1">{s.label}</h2>
            <p className="text-sm text-gray-500">{s.description}</p>
          </a>
        ))}
      </nav>
    </main>
  );
}
