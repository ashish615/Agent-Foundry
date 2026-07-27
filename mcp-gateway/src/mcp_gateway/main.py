from fastapi import FastAPI

app = FastAPI(
    title="Agent Foundry — MCP Gateway",
    version="0.1.0",
    description="MCP server registry and proxy: route agent tool calls, inject credentials, enforce access control.",
)


@app.get("/v1/health")
async def health() -> dict:
    return {"status": "ok", "service": "mcp-gateway"}
