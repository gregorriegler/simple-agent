import pytest
from textual.containers import VerticalScroll
from textual.widgets import Markdown, TextArea

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AssistantSaidEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog

from tests.infrastructure.textual.conftest import StubTool


def _last_markdown_text(app: TextualApp, agent_id: AgentId) -> str:
    _, log_id, _ = app.panel_ids_for(agent_id)
    scroll = app.query_one(f"#{log_id}-scroll", VerticalScroll)
    markdowns = list(scroll.query(Markdown))
    return markdowns[-1]._markdown


def _latest_tool_text_area(app: TextualApp, agent_id: AgentId) -> TextArea:
    _, _, tool_results_id = app.panel_ids_for(agent_id)
    tool_log = app.query_one(f"#{tool_results_id}", ToolLog)
    collapsible = tool_log._collapsibles[-1]
    return collapsible.query_one(TextArea)


@pytest.mark.asyncio
async def test_domain_event_message_wraps_event():
    event = SessionStartedEvent(AgentId("Agent"), False)

    message = DomainEventMessage(event)

    assert message.event is event


@pytest.mark.asyncio
async def test_session_start_message_is_logged(textual_harness):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")

    async with app.run_test() as pilot:
        await pilot.pause()

        event_bus.publish(SessionStartedEvent(agent_id, False))
        await pilot.pause()

        assert _last_markdown_text(app, agent_id) == "Starting new session"


@pytest.mark.asyncio
async def test_user_prompt_requested_message_is_logged(textual_harness):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")

    async with app.run_test() as pilot:
        await pilot.pause()

        event_bus.publish(UserPromptRequestedEvent(agent_id))
        await pilot.pause()

        assert _last_markdown_text(app, agent_id) == "\nWaiting for user input..."


@pytest.mark.asyncio
async def test_user_prompted_file_context_is_compacted(textual_harness):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")
    input_text = (
        'Please check <file_context path="notes.md">\nNote contents\n</file_context>'
    )

    async with app.run_test() as pilot:
        await pilot.pause()

        event_bus.publish(UserPromptedEvent(agent_id, input_text))
        await pilot.pause()

        assert (
            _last_markdown_text(app, agent_id) == "**User:** Please check\n[📦notes.md]"
        )


@pytest.mark.asyncio
async def test_assistant_message_is_logged(textual_harness):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")

    async with app.run_test() as pilot:
        await pilot.pause()

        event_bus.publish(AssistantSaidEvent(agent_id, "Hello"))
        await pilot.pause()

        assert _last_markdown_text(app, agent_id) == "**Agent:** Hello"


@pytest.mark.asyncio
async def test_tool_call_and_result_are_tracked(textual_harness):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")
    call_id = "call-1"

    async with app.run_test() as pilot:
        await pilot.pause()

        event_bus.publish(ToolCalledEvent(agent_id, call_id, StubTool()))
        await pilot.pause()

        _, _, tool_results_id = app.panel_ids_for(agent_id)
        tool_log = app.query_one(f"#{tool_results_id}", ToolLog)
        assert call_id in tool_log._pending_tool_calls

        event_bus.publish(
            ToolResultEvent(agent_id, call_id, SingleToolResult(message="Done"))
        )
        await pilot.pause()

        assert call_id not in tool_log._pending_tool_calls
        assert _latest_tool_text_area(app, agent_id).text == "Done"


@pytest.mark.asyncio
async def test_submit_input_sends_user_input(textual_harness):
    _, _, user_input, app = textual_harness

    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.query_one("#user-input", TextArea)

        text_area.text = "Hello"

        app.action_submit_input()
        await pilot.pause()

        assert user_input.submissions == ["Hello"]
        assert text_area.text == ""
