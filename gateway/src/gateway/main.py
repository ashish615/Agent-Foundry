from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import Settings

settings = Settings()

app = FastAPI(
    title="Agent Foundry — AI Gateway",
    version="0.1.0",
    description="Central reverse-proxy for all AI requests: routing, rate limiting, guardrails, budget controls.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/health")
async def health() -> dict:
    return {"status": "ok", "service": "gateway"}
