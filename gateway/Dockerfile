FROM python:3.11-slim AS build
WORKDIR /app
# Build context is the repo root — copy only what pip needs
COPY gateway/pyproject.toml .
COPY gateway/src/ src/
RUN pip install --no-cache-dir .

FROM python:3.11-slim
WORKDIR /app
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
# Shared ORM models live in migrations/ — put them on PYTHONPATH so `import models` works
# without duplicating model definitions inside the service (CLAUDE.md constraint).
COPY migrations/ /migrations/
ENV PYTHONPATH=/migrations
EXPOSE 8000
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
