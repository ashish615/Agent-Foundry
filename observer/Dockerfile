FROM python:3.11-slim AS build
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir hatchling && pip install --no-cache-dir -e .

FROM python:3.11-slim
WORKDIR /app
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
COPY src/ src/
EXPOSE 9090
CMD ["python", "-m", "observer.main"]
