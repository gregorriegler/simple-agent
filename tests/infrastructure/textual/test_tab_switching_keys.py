import pytest
from textual.widgets import TabbedContent

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import AgentStartedEvent
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs
from tests.infrastructure.textual.test_utils import MockUserInput

@pytest.fixture
def app(agent_task_manager):
    return TextualApp(MockUserInput(), AgentId("Agent"), agent_task_manager)

@pytest.mark.asyncio
async def test_tab_switching_keys(app: TextualApp):
    root_agent = AgentId("Agent")
    subagent = AgentId("Agent/Sub")

    async with app.run_test() as pilot:
        await pilot.pause()

        app.on_domain_event_message(
            DomainEventMessage(AgentStartedEvent(root_agent, "Agent", "dummy-model"))
        )
        await pilot.pause()
        app.add_subagent_tab(subagent, "Sub")
        await pilot.pause()

        tabs = app.query_one(AgentTabs)
        root_tab_id = app.panel_ids_for(root_agent)[0]
        sub_tab_id = app.panel_ids_for(subagent)[0]

        assert tabs.active == root_tab_id

        # Verify SmartInput focus
        workspace = tabs.active_workspace
        assert workspace.smart_input.has_focus

        # Test Alt+Right (Next)
        await pilot.press("alt+right")
        await pilot.pause()
        assert tabs.active == sub_tab_id

        # Test Alt+Left (Previous)
        await pilot.press("alt+left")
        await pilot.pause()
        assert tabs.active == root_tab_id

        # Test Alt+Down (Next)
        await pilot.press("alt+down")
        await pilot.pause()
        assert tabs.active == sub_tab_id

        # Test Alt+Up (Previous)
        await pilot.press("alt+up")
        await pilot.pause()
        assert tabs.active == root_tab_id

        # Test Ctrl+PageDown (Next)
        await pilot.press("ctrl+page_down")
        await pilot.pause()
        assert tabs.active == sub_tab_id

        # Test Ctrl+PageUp (Previous)
        await pilot.press("ctrl+page_up")
        await pilot.pause()
        assert tabs.active == root_tab_id
