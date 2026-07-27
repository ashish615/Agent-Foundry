"""Tests for AgentFoundry SDK client."""

import json
import pytest
import httpx
import respx

from agent_foundry.client import AgentFoundry, _ModelsClient, _GatewayClient, _AgentsClient


# ── Initialization ──────────────────────────────────────────────────────────────

class TestAgentFoundryInit:
    def test_sub_clients_are_created(self):
        client = AgentFoundry(api_key="test-key")
        assert isinstance(client.models, _ModelsClient)
        assert isinstance(client.gateway, _GatewayClient)
        assert isinstance(client.agents, _AgentsClient)

    def test_default_base_url(self):
        client = AgentFoundry(api_key="test-key")
        assert str(client._http.base_url) == "http://localhost:8000"

    def test_custom_base_url(self):
        client = AgentFoundry(api_key="test-key", base_url="https://api.prod.example.com")
        assert "api.prod.example.com" in str(client._http.base_url)

    def test_bearer_token_in_auth_header(self):
        client = AgentFoundry(api_key="my-secret-key")
        assert client._http.headers["authorization"] == "Bearer my-secret-key"

    def test_different_keys_produce_different_headers(self):
        c1 = AgentFoundry(api_key="key-one")
        c2 = AgentFoundry(api_key="key-two")
        assert c1._http.headers["authorization"] != c2._http.headers["authorization"]

    async def test_async_context_manager_returns_self(self):
        async with AgentFoundry(api_key="test-key") as client:
            assert isinstance(client, AgentFoundry)

    async def test_async_context_manager_closes_http_client(self):
        af = AgentFoundry(api_key="test-key")
        async with af:
            pass
        assert af._http.is_closed


# ── _ModelsClient ───────────────────────────────────────────────────────────────

class TestModelsClient:
    @respx.mock
    async def test_list_returns_models(self):
        respx.get("http://localhost:8000/v1/models").mock(
            return_value=httpx.Response(200, json=[
                {"slug": "gpt-4o", "provider": "openai"},
                {"slug": "claude-3-5-sonnet", "provider": "anthropic"},
            ])
        )
        client = AgentFoundry(api_key="key")
        result = await client.models.list()
        assert len(result) == 2
        assert result[0]["slug"] == "gpt-4o"
        assert result[1]["provider"] == "anthropic"

    @respx.mock
    async def test_list_returns_empty_list(self):
        respx.get("http://localhost:8000/v1/models").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await AgentFoundry(api_key="key").models.list()
        assert result == []

    @respx.mock
    async def test_list_raises_on_401_unauthorized(self):
        respx.get("http://localhost:8000/v1/models").mock(
            return_value=httpx.Response(401, json={"detail": "Unauthorized"})
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await AgentFoundry(api_key="bad-key").models.list()
        assert exc_info.value.response.status_code == 401

    @respx.mock
    async def test_list_raises_on_500_server_error(self):
        respx.get("http://localhost:8000/v1/models").mock(
            return_value=httpx.Response(500)
        )
        with pytest.raises(httpx.HTTPStatusError):
            await AgentFoundry(api_key="key").models.list()

    @respx.mock
    async def test_list_sends_bearer_token(self):
        route = respx.get("http://localhost:8000/v1/models").mock(
            return_value=httpx.Response(200, json=[])
        )
        await AgentFoundry(api_key="tok-abc").models.list()
        assert route.calls[0].request.headers["authorization"] == "Bearer tok-abc"


# ── _GatewayClient ──────────────────────────────────────────────────────────────

class TestGatewayClient:
    @respx.mock
    async def test_chat_returns_response(self):
        expected = {
            "id": "chatcmpl-xyz",
            "object": "chat.completion",
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
        }
        respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=expected)
        )
        result = await AgentFoundry(api_key="key").gateway.chat(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert result["id"] == "chatcmpl-xyz"
        assert result["choices"][0]["message"]["content"] == "Hello!"

    @respx.mock
    async def test_chat_sends_model_and_messages(self):
        route = respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": []})
        )
        await AgentFoundry(api_key="key").gateway.chat(
            model="llama-3-8b",
            messages=[{"role": "user", "content": "Tell me a joke"}],
        )
        body = json.loads(route.calls[0].request.content)
        assert body["model"] == "llama-3-8b"
        assert body["messages"][0]["content"] == "Tell me a joke"

    @respx.mock
    async def test_chat_forwards_extra_kwargs(self):
        route = respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": []})
        )
        await AgentFoundry(api_key="key").gateway.chat(
            model="gpt-4o",
            messages=[],
            temperature=0.2,
            max_tokens=512,
        )
        body = json.loads(route.calls[0].request.content)
        assert body["temperature"] == 0.2
        assert body["max_tokens"] == 512

    @respx.mock
    async def test_chat_raises_on_429_rate_limit(self):
        respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "60"})
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await AgentFoundry(api_key="key").gateway.chat(model="gpt-4o", messages=[])
        assert exc_info.value.response.status_code == 429

    @respx.mock
    async def test_chat_raises_on_402_budget_exceeded(self):
        respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(402, json={"detail": "Budget exceeded"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await AgentFoundry(api_key="key").gateway.chat(model="gpt-4o", messages=[])

    @respx.mock
    async def test_chat_with_empty_messages(self):
        respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": []})
        )
        result = await AgentFoundry(api_key="key").gateway.chat(model="gpt-4o", messages=[])
        assert result == {"choices": []}

    @respx.mock
    async def test_chat_sends_bearer_token(self):
        route = respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": []})
        )
        await AgentFoundry(api_key="tok-xyz").gateway.chat(model="m", messages=[])
        assert route.calls[0].request.headers["authorization"] == "Bearer tok-xyz"


# ── _AgentsClient ───────────────────────────────────────────────────────────────

class TestAgentsClient:
    @respx.mock
    async def test_list_returns_agents(self):
        respx.get("http://localhost:8000/v1/agents").mock(
            return_value=httpx.Response(200, json=[
                {"id": "ag-1", "name": "support-bot", "framework": "langgraph"},
                {"id": "ag-2", "name": "data-agent", "framework": "crewai"},
            ])
        )
        result = await AgentFoundry(api_key="key").agents.list()
        assert len(result) == 2
        assert result[0]["framework"] == "langgraph"
        assert result[1]["name"] == "data-agent"

    @respx.mock
    async def test_list_returns_empty_list(self):
        respx.get("http://localhost:8000/v1/agents").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await AgentFoundry(api_key="key").agents.list()
        assert result == []

    @respx.mock
    async def test_list_raises_on_403_forbidden(self):
        respx.get("http://localhost:8000/v1/agents").mock(
            return_value=httpx.Response(403, json={"detail": "Forbidden"})
        )
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await AgentFoundry(api_key="key").agents.list()
        assert exc_info.value.response.status_code == 403

    @respx.mock
    async def test_list_sends_bearer_token(self):
        route = respx.get("http://localhost:8000/v1/agents").mock(
            return_value=httpx.Response(200, json=[])
        )
        await AgentFoundry(api_key="agent-tok").agents.list()
        assert route.calls[0].request.headers["authorization"] == "Bearer agent-tok"
