"""Protocol interfaces for agent framework adapters."""

from typing import AsyncIterator, Protocol
from pydantic import BaseModel


class AgentTask(BaseModel):
    run_id: str
    agent_id: str
    input: str
    context: dict = {}


class AgentEvent(BaseModel):
    run_id: str
    type: str  # e.g. "step", "tool_call", "llm_response", "complete", "error", "PAUSE_FOR_HUMAN"
    payload: dict = {}


class AgentRunner(Protocol):
    async def run(self, task: AgentTask) -> AsyncIterator[AgentEvent]: ...
    async def pause(self, run_id: str) -> None: ...
    async def resume(self, run_id: str, input: str) -> None: ...
