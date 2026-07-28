from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import engine
from .routers import auth, keys, orgs
from .settings import Settings

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Agent Foundry — AI Gateway",
    version="0.1.0",
    description="Central reverse-proxy for all AI requests: routing, rate limiting, guardrails, budget controls.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(orgs.router)
app.include_router(keys.router)


@app.get("/v1/health")
async def health() -> dict:
    return {"status": "ok", "service": "gateway"}
