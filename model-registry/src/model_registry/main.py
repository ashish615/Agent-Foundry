from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import engine
from .routers import models
from .settings import Settings

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Agent Foundry — Model Registry",
    version="0.1.0",
    description="Model catalog: commercial connectors, OSS serving (vLLM), fine-tuning jobs.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models.router)


@app.get("/v1/health")
async def health() -> dict:
    return {"status": "ok", "service": "model-registry"}
