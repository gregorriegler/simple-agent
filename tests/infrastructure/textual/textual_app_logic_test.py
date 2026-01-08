from unittest.mock import patch

import pytest
from textual.widgets import TabbedContent

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AssistantSaidEvent,
    SessionClearedEvent,
    ToolResultEvent,
)
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from tests.infrastructure.textual.test_utils import MockUserInput


@pytest.fixture
def app():
    return TextualApp(SlashCommandRegistry(), MockUserInput(), AgentId("Agent"))


@pytest.mark.asyncio
async def test_switch_tabs_cycles_between_root_and_subagent(app: TextualApp):
    root_agent = AgentId("Agent")
    subagent = AgentId("Agent/Sub")

    async with app.run_test() as pilot:
        await pilot.pause()

        app.add_subagent_tab(subagent, "Sub")
        await pilot.pause()

        tabs = app.query_one("#tabs", TabbedContent)
        assert tabs.active == app.panel_ids_for(subagent)[0]

        app.action_next_tab()
        assert tabs.active == app.panel_ids_for(root_agent)[0]

        app.action_previous_tab()
        assert tabs.active == app.panel_ids_for(subagent)[0]


@pytest.mark.asyncio
async def test_textual_app_lifecycle(app: TextualApp):
    async with app.run_test():
        # Test action_quit
        with patch.object(app, "exit") as mock_exit:
            await app.action_quit()
            mock_exit.assert_called_once()

        # Test shutdown
        with patch.object(app, "exit") as mock_exit:
            # We need to mock is_running=True ideally, but it should be true in test
            app.shutdown()
            mock_exit.assert_called_once()


@pytest.mark.asyncio
async def test_textual_app_write_tool_result_no_pending(app: TextualApp):
    async with app.run_test():
        agent_id = AgentId("Agent")
        _, _, tool_results_id = app.panel_ids_for(agent_id)

        # Write result with no call
        result = SingleToolResult(message="Done")
        app.on_domain_event_message(
            DomainEventMessage(ToolResultEvent(agent_id, "unknown-call", result))
        )
        # Should just log warning and not crash


@pytest.mark.asyncio
async def test_textual_app_clear_panels(app: TextualApp):
    async with app.run_test() as pilot:
        agent_id = AgentId("Agent")
        _, log_id, _ = app.panel_ids_for(agent_id)

        # Add content via event
        app.on_domain_event_message(
            DomainEventMessage(AssistantSaidEvent(agent_id, "Message"))
        )
        await pilot.pause()

        # Clear via event
        app.on_domain_event_message(DomainEventMessage(SessionClearedEvent(agent_id)))
        await pilot.pause()

        # Verify cleared
        scroll = app.query_one(f"#{log_id}-scroll")
        assert len(scroll.children) == 0
