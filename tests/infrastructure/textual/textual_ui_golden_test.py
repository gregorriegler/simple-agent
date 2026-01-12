from typing import cast

import pytest
from approvaltests import verify
from textual.timer import Timer

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AssistantSaidEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptedEvent,
    UserPromptRequestedEvent,
)
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog
from tests.infrastructure.textual.test_utils import dump_ascii_screen, dump_ui_state


@pytest.mark.asyncio
async def test_golden_happy_path_flow(tmp_path, monkeypatch):
    """
    Run a full happy path flow and verify the UI state at every step.
    This creates a visual timeline of the user session.
    Flow:
    1. Session Start
    2. User Prompt Requested
    3. User Types "Hello"
    4. Assistant Says "Hi"
    5. Assistant Calls Tool
    6. Tool Returns Result
    """

    class DummyTimer:
        def stop(self) -> None:
            return None

    def noop_set_interval(*args: object, **kwargs: object) -> Timer:
        return cast(Timer, DummyTimer())

    # Disable timers on ToolLog to prevent non-deterministic loading animations
    monkeypatch.setattr(ToolLog, "set_interval", noop_set_interval)

    agent_id = AgentId("Agent", root=tmp_path)
    app = TextualApp(user_input=None, root_agent_id=agent_id)

    # Disable loading timer to avoid non-determinism
    # We can mock set_interval on the app or just ensure we don't wait for it
    # But better to prevent it from updating state asynchronously
    app.set_interval = noop_set_interval

    timeline = []

    def capture_step(step_name: str):
        # Dump Widget Tree
        timeline.append(f"--- Step: {step_name} (Widget Tree) ---")
        timeline.append(dump_ui_state(app))
        timeline.append("")

        # Dump ASCII Screen
        timeline.append(f"--- Step: {step_name} (ASCII UI) ---")
        timeline.append(dump_ascii_screen(app))
        timeline.append("")

    async with app.run_test(size=(80, 24)) as pilot:
        # 1. Session Start (Initial state)
        # Note: In a real run, the session might start automatically or via an event.
        # We inject the event to simulate the backend starting the session.
        app.on_domain_event_message(
            DomainEventMessage(SessionStartedEvent(agent_id, False))
        )
        await pilot.pause()
        capture_step("Session Started")

        # 2. User Prompt Requested
        app.on_domain_event_message(
            DomainEventMessage(UserPromptRequestedEvent(agent_id))
        )
        await pilot.pause()
        capture_step("User Prompt Requested")

        # 3. User prompts "Hello"
        # Drive the UI properly: Focus input, Type "Hello", Press Enter
        await pilot.click("#user-input-Agent")
        await pilot.press(*list("Hello"))
        await pilot.press("enter")
        await pilot.pause()
        capture_step("User Input Submitted")

        # 4. Assistant Reply
        # We still need to inject the backend events as we don't have a real backend connected in this unit test.
        # But for the User Input part, we now verified the Input -> Event flow (partially, if we had a listener).
        # Wait, if we use pilot.press, the TextualApp will trigger `submit_input`.
        # We need to verify that `submit_input` was called or that the UI reacted (cleared input).

        # Inject response to move flow forward
        app.on_domain_event_message(
            DomainEventMessage(UserPromptedEvent(agent_id, "Hello"))
        )
        app.on_domain_event_message(
            DomainEventMessage(AssistantSaidEvent(agent_id, "Hi there!"))
        )
        await pilot.pause()
        capture_step("Assistant Reply")

        # 5. Assistant Calls Tool
        call_id = "call-1"
        tool_header = "search_files(query='test')"
        app.on_domain_event_message(
            DomainEventMessage(
                ToolCalledEvent(
                    agent_id,
                    call_id,
                    type("Tool", (), {"header": lambda s: tool_header})(),
                )
            )
        )
        await pilot.pause()
        capture_step("Tool Called")

        # 6. Tool Returns Result
        result = SingleToolResult(
            message="Found 1 file.", display_title="Search Results"
        )
        app.on_domain_event_message(
            DomainEventMessage(ToolResultEvent(agent_id, call_id, result))
        )
        await pilot.pause()
        capture_step("Tool Result")

        # Verify Timeline
        verify("\n".join(timeline))
