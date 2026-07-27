from fastapi import FastAPI

app = FastAPI(
    title="Agent Foundry — Agent Runtime",
    version="0.1.0",
    description="Deploy and execute agents across LangGraph, CrewAI, AutoGen, and custom frameworks.",
)


@app.get("/v1/health")
async def health() -> dict:
    return {"status": "ok", "service": "agent-runtime"}
