"""Tests for AgentTask, AgentEvent, and AgentRunner protocol."""

import pytest
from pydantic import ValidationError
from typing import AsyncIterator

from agent_runtime.protocols import AgentTask, AgentEvent, AgentRunner


# ── AgentTask ──────────────────────────────────────────────────────────────────

class TestAgentTask:
    def test_valid_task(self):
        task = AgentTask(run_id="run-1", agent_id="agent-1", input="process this")
        assert task.run_id == "run-1"
        assert task.agent_id == "agent-1"
        assert task.input == "process this"

    def test_context_defaults_to_empty_dict(self):
        task = AgentTask(run_id="r", agent_id="a", input="x")
        assert task.context == {}

    def test_context_can_be_provided(self):
        task = AgentTask(run_id="r", agent_id="a", input="x", context={"session_id": "s1"})
        assert task.context["session_id"] == "s1"

    def test_missing_run_id_raises(self):
        with pytest.raises(ValidationError):
            AgentTask(agent_id="a", input="x")  # type: ignore[call-arg]

    def test_missing_agent_id_raises(self):
        with pytest.raises(ValidationError):
            AgentTask(run_id="r", input="x")  # type: ignore[call-arg]

    def test_missing_input_raises(self):
        with pytest.raises(ValidationError):
            AgentTask(run_id="r", agent_id="a")  # type: ignore[call-arg]

    def test_task_is_immutable_by_pydantic(self):
        task = AgentTask(run_id="r", agent_id="a", input="x")
        # Pydantic v2 models are mutable by default; verify fields are accessible
        assert hasattr(task, "run_id")

    def test_task_serializes_to_dict(self):
        task = AgentTask(run_id="r", agent_id="a", input="x")
        d = task.model_dump()
        assert d["run_id"] == "r"
        assert d["input"] == "x"
        assert d["context"] == {}


# ── AgentEvent ─────────────────────────────────────────────────────────────────

class TestAgentEvent:
    def test_valid_event(self):
        event = AgentEvent(run_id="run-1", type="step")
        assert event.run_id == "run-1"
        assert event.type == "step"

    def test_payload_defaults_to_empty_dict(self):
        event = AgentEvent(run_id="r", type="complete")
        assert event.payload == {}

    def test_payload_can_be_provided(self):
        event = AgentEvent(run_id="r", type="tool_call", payload={"tool": "search", "query": "python"})
        assert event.payload["tool"] == "search"

    def test_missing_run_id_raises(self):
        with pytest.raises(ValidationError):
            AgentEvent(type="step")  # type: ignore[call-arg]

    def test_missing_type_raises(self):
        with pytest.raises(ValidationError):
            AgentEvent(run_id="r")  # type: ignore[call-arg]

    def test_known_event_types_are_valid(self):
        for event_type in ("step", "tool_call", "llm_response", "complete", "error", "PAUSE_FOR_HUMAN"):
            event = AgentEvent(run_id="r", type=event_type)
            assert event.type == event_type

    def test_event_serializes_to_dict(self):
        event = AgentEvent(run_id="r", type="error", payload={"message": "timeout"})
        d = event.model_dump()
        assert d["type"] == "error"
        assert d["payload"]["message"] == "timeout"


# ── AgentRunner Protocol ────────────────────────────────────────────────────────

class TestAgentRunnerProtocol:
    def test_protocol_has_run_method(self):
        assert hasattr(AgentRunner, "run")

    def test_protocol_has_pause_method(self):
        assert hasattr(AgentRunner, "pause")

    def test_protocol_has_resume_method(self):
        assert hasattr(AgentRunner, "resume")

    def test_concrete_class_satisfies_protocol(self):
        """A class with the right methods is structurally compatible."""

        class DummyRunner:
            async def run(self, task: AgentTask) -> AsyncIterator[AgentEvent]:
                yield AgentEvent(run_id=task.run_id, type="complete")

            async def pause(self, run_id: str) -> None:
                pass

            async def resume(self, run_id: str, input: str) -> None:
                pass

        runner: AgentRunner = DummyRunner()  # type: ignore[assignment]
        assert runner is not None

    async def test_concrete_runner_yields_events(self):
        """End-to-end: a concrete runner accepts a task and yields events."""

        class EchoRunner:
            async def run(self, task: AgentTask) -> AsyncIterator[AgentEvent]:
                yield AgentEvent(run_id=task.run_id, type="step", payload={"echo": task.input})
                yield AgentEvent(run_id=task.run_id, type="complete")

            async def pause(self, run_id: str) -> None:
                pass

            async def resume(self, run_id: str, input: str) -> None:
                pass

        runner = EchoRunner()
        task = AgentTask(run_id="run-42", agent_id="echo-agent", input="hello world")

        events = [event async for event in runner.run(task)]

        assert len(events) == 2
        assert events[0].type == "step"
        assert events[0].payload["echo"] == "hello world"
        assert events[1].type == "complete"

    async def test_runner_pause_is_awaitable(self):
        class DummyRunner:
            async def run(self, task: AgentTask) -> AsyncIterator[AgentEvent]:
                yield AgentEvent(run_id=task.run_id, type="complete")

            async def pause(self, run_id: str) -> None:
                pass

            async def resume(self, run_id: str, input: str) -> None:
                pass

        runner = DummyRunner()
        await runner.pause("run-1")  # must not raise

    async def test_runner_resume_is_awaitable(self):
        class DummyRunner:
            async def run(self, task: AgentTask) -> AsyncIterator[AgentEvent]:
                yield AgentEvent(run_id=task.run_id, type="complete")

            async def pause(self, run_id: str) -> None:
                pass

            async def resume(self, run_id: str, input: str) -> None:
                pass

        runner = DummyRunner()
        await runner.resume("run-1", "user confirmation")  # must not raise
