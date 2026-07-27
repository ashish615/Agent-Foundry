from fastapi import FastAPI

app = FastAPI(
    title="Agent Foundry — Model Registry",
    version="0.1.0",
    description="Model catalog: commercial connectors, OSS serving (vLLM), fine-tuning jobs.",
)


@app.get("/v1/health")
async def health() -> dict:
    return {"status": "ok", "service": "model-registry"}
