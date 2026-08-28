import pytest
from approvaltests import verify
from textual.widgets import Collapsible

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentStartedEvent,
    AssistantThoughtEvent,
    ToolCalledEvent,
    ToolResultEvent,
)
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog
from tests.infrastructure.textual.conftest import StubTool
from tests.infrastructure.textual.test_utils import dump_ui_state


def _left_borders(app, agent_id: AgentId) -> list[tuple]:
    _, _, tool_results_id = app.panel_ids_for(agent_id)
    tool_log = app.query_one(f"#{tool_results_id}", ToolLog)
    collapsible = tool_log._collapsibles[-1]
    title = collapsible.query_one(Collapsible.Contents).parent.children[0]
    contents = collapsible.query_one(Collapsible.Contents)
    return [title.styles.border_left, contents.styles.border_left]


@pytest.mark.asyncio
async def test_a_thought_is_shown_in_the_tool_log_before_the_call_it_led_to(
    textual_harness,
):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")

    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
        await pilot.pause()
        event_bus.publish(
            AssistantThoughtEvent(agent_id, "The file is small, I will read it whole.")
        )
        event_bus.publish(ToolCalledEvent(agent_id, "call-1", StubTool()))
        await pilot.pause()

        verify(dump_ui_state(app))


@pytest.mark.asyncio
async def test_the_left_border_runs_past_the_header_down_the_expanded_content(
    textual_harness,
):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")

    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
        event_bus.publish(ToolCalledEvent(agent_id, "call-1", StubTool()))
        event_bus.publish(
            ToolResultEvent(agent_id, "call-1", SingleToolResult("all good"))
        )
        await pilot.pause()

        title_border, contents_border = _left_borders(app, agent_id)

        assert contents_border == title_border
