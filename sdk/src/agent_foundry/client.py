import httpx


class AgentFoundry:
    """Top-level SDK client."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000") -> None:
        self._api_key = api_key
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        self.models = _ModelsClient(self._http)
        self.gateway = _GatewayClient(self._http)
        self.agents = _AgentsClient(self._http)

    async def __aenter__(self) -> "AgentFoundry":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._http.aclose()


class _ModelsClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def list(self) -> list[dict]:
        r = await self._http.get("/v1/models")
        r.raise_for_status()
        return r.json()


class _GatewayClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def chat(self, model: str, messages: list[dict], **kwargs: object) -> dict:
        r = await self._http.post(
            "/v1/chat/completions",
            json={"model": model, "messages": messages, **kwargs},
        )
        r.raise_for_status()
        return r.json()


class _AgentsClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def list(self) -> list[dict]:
        r = await self._http.get("/v1/agents")
        r.raise_for_status()
        return r.json()
