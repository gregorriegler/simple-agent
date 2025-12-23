import pytest
from textual.widgets import TabbedContent, TextArea, Static

from simple_agent.application.agent_id import AgentId
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.textual.textual_app import TextualApp


class FakeUserInput:
    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def submit_input(self, content: str) -> None:
        return None

    def close(self) -> None:
        return None


@pytest.fixture
def app():
    return TextualApp(FakeUserInput(), AgentId("Agent"))


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
async def test_write_tool_result_renders_diff_as_static(app: TextualApp):
    agent_id = AgentId("Agent")
    _, _, tool_results_id = app.panel_ids_for(agent_id)
    call_id = "call-1"

    async with app.run_test() as pilot:
        await pilot.pause()

        app.write_tool_call(tool_results_id, call_id, "Tool Call\nInput: example")
        result = SingleToolResult(message="@@ -1 +1 @@\n-test\n+passed", display_language="diff")
        app.write_tool_result(tool_results_id, call_id, result)
        await pilot.pause()

        collapsible = app._tool_result_collapsibles[tool_results_id][-1]
        assert collapsible.query_one(Static)


@pytest.mark.asyncio
async def test_write_tool_cancelled_marks_call_as_cancelled(app: TextualApp):
    agent_id = AgentId("Agent")
    _, _, tool_results_id = app.panel_ids_for(agent_id)
    call_id = "call-1"

    async with app.run_test() as pilot:
        await pilot.pause()

        app.write_tool_call(tool_results_id, call_id, "Tool Call\nInput: example")
        app.write_tool_cancelled(tool_results_id, call_id)
        await pilot.pause()

        collapsible = app._tool_result_collapsibles[tool_results_id][-1]
        text_area = collapsible.query_one(TextArea)
        assert text_area.text == "Cancelled"
        assert collapsible.title.endswith("(Cancelled)")


@pytest.mark.asyncio
async def test_write_tool_call_suppresses_write_todos(app: TextualApp):
    agent_id = AgentId("Agent")
    _, _, tool_results_id = app.panel_ids_for(agent_id)
    call_id = "call-1"

    async with app.run_test() as pilot:
        await pilot.pause()

        app.write_tool_call(tool_results_id, call_id, "write-todos\nInput: example")
        assert call_id not in app._pending_tool_calls[tool_results_id]
        assert call_id in app._suppressed_tool_calls

        result = SingleToolResult(message="Done")
        app.write_tool_result(tool_results_id, call_id, result)
        assert call_id not in app._suppressed_tool_calls
