from fastapi import FastAPI

app = FastAPI(
    title="Agent Foundry — Observer",
    version="0.1.0",
    description="Telemetry collection, cost analytics, and Grafana dashboard provisioning.",
)


@app.get("/v1/health")
async def health() -> dict:
    return {"status": "ok", "service": "observer"}
