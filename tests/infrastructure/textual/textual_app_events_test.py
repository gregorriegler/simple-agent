import pytest
from textual.containers import VerticalScroll
from textual.widgets import Collapsible, Markdown, TextArea

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentChangedEvent,
    AgentStartedEvent,
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
from tests.infrastructure.textual.conftest import StubTool
from tests.infrastructure.textual.test_utils import eventually


def _last_markdown_text(app: TextualApp, agent_id: AgentId) -> str:
    _, log_id, _ = app.panel_ids_for(agent_id)
    scroll = app.query_one(f"#{log_id}-scroll", VerticalScroll)
    markdowns = list(scroll.query(Markdown))
    return markdowns[-1]._markdown


def _tool_log(app: TextualApp, agent_id: AgentId) -> ToolLog:
    _, _, tool_results_id = app.panel_ids_for(agent_id)
    return app.query_one(f"#{tool_results_id}", ToolLog)


def _latest_tool_collapsible(app: TextualApp, agent_id: AgentId) -> Collapsible:
    return _tool_log(app, agent_id)._collapsibles[-1]


def _latest_tool_text_area(app: TextualApp, agent_id: AgentId) -> TextArea:
    return _latest_tool_collapsible(app, agent_id).query_one(TextArea)


@pytest.mark.asyncio
async def test_tool_call_loading_indicator_has_border_and_transparent_background(
    textual_harness,
):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")
    call_id = "test-call-id"

    async with app.run_test() as pilot:
        await pilot.pause()
        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
        await pilot.pause()
        event_bus.publish(ToolCalledEvent(agent_id, call_id, StubTool()))

        await eventually(
            pilot,
            lambda: _latest_tool_text_area(app, agent_id)._cover_widget is not None,
            "the loading indicator to cover the tool call",
        )

        cover = _latest_tool_text_area(app, agent_id)._cover_widget
        assert cover.styles.border.top[0] == "round"
        assert cover.styles.background.is_transparent


@pytest.mark.asyncio
async def test_tool_call_collapsible_content_starts_at_left_edge(textual_harness):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")
    call_id = "test-call-id"

    async with app.run_test() as pilot:
        await pilot.pause()
        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
        await pilot.pause()
        event_bus.publish(ToolCalledEvent(agent_id, call_id, StubTool()))

        await eventually(
            pilot,
            lambda: len(
                _latest_tool_collapsible(app, agent_id).query(Collapsible.Contents)
            )
            == 1,
            "the tool call collapsible to mount its contents",
        )

        collapsible = _latest_tool_collapsible(app, agent_id)
        contents = collapsible.query_one(Collapsible.Contents)

        assert collapsible.styles.padding.left == 0
        assert contents.styles.padding.left == 0
        assert collapsible.styles.border.top[0] in ("", "none")


@pytest.mark.asyncio
async def test_tool_call_collapsible_title_takes_full_width_for_word_wrap(
    textual_harness,
):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")
    call_id = "test-call-id"

    class LongTitleTool:
        def header(self) -> str:
            return "🛠️ bash " + "long_argument " * 20

    async with app.run_test() as pilot:
        await pilot.pause()
        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
        await pilot.pause()
        event_bus.publish(ToolCalledEvent(agent_id, call_id, LongTitleTool()))

        await eventually(
            pilot,
            lambda: _latest_tool_collapsible(app, agent_id)._title.size.height > 1,
            "the long tool call title to wrap onto more than one line",
        )

        title_widget = _latest_tool_collapsible(app, agent_id)._title
        assert title_widget.styles.width.value == 100.0


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

        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
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

        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
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

        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
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

        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
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

        event_bus.publish(AgentStartedEvent(agent_id, "Agent", "dummy-model"))
        await pilot.pause()
        event_bus.publish(ToolCalledEvent(agent_id, call_id, StubTool()))

        await eventually(
            pilot,
            lambda: call_id in _tool_log(app, agent_id)._pending_tool_calls,
            "the tool call to be tracked as pending",
        )

        event_bus.publish(
            ToolResultEvent(agent_id, call_id, SingleToolResult(message="Done"))
        )

        await eventually(
            pilot,
            lambda: call_id not in _tool_log(app, agent_id)._pending_tool_calls,
            "the tool result to settle the pending call",
        )

        assert _latest_tool_text_area(app, agent_id).text == "Done"


@pytest.mark.asyncio
async def test_submit_input_sends_user_input(textual_harness):
    _, _, user_input, app = textual_harness

    async with app.run_test() as pilot:
        await pilot.pause()
        # Find the active smart input
        from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs

        workspace = app.query_one(AgentTabs).active_workspace
        text_area = workspace.smart_input

        text_area.text = "Hello"

        app.action_submit_input()

        await eventually(
            pilot,
            lambda: user_input.submissions == ["Hello"],
            "the submitted input to reach the user input port",
        )

        assert text_area.text == ""


@pytest.mark.asyncio
async def test_agent_started_creates_tab_with_model_in_title(textual_harness):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")

    async with app.run_test() as pilot:
        await pilot.pause()

        event_bus.publish(AgentStartedEvent(agent_id, "MyAgent", "test-model"))
        await pilot.pause()

        tabs = app.query_one("#tabs")
        tab_id, _, _ = app.panel_ids_for(agent_id)
        tab = tabs.get_tab(tab_id)

        # When model is set without token info, it should default to 0.0% if it was not set previously.
        # But our implementation might show "MyAgent [test-model]" if token usage is empty string.
        # Since I am updating the implementation to respect the test expectation:
        assert str(tab.label) == "MyAgent [test-model]"


@pytest.mark.asyncio
async def test_agent_changed_event_updates_tab_title(textual_harness):
    event_bus, _, _, app = textual_harness
    agent_id = AgentId("Agent")

    async with app.run_test() as pilot:
        await pilot.pause()

        event_bus.publish(AgentStartedEvent(agent_id, "MyAgent", "test-model"))
        await pilot.pause()
        event_bus.publish(
            AgentChangedEvent(
                agent_id=agent_id,
                old_name="MyAgent",
                new_name="Developer",
            )
        )
        await pilot.pause()

        tabs = app.query_one("#tabs")
        tab_id, _, _ = app.panel_ids_for(agent_id)
        tab = tabs.get_tab(tab_id)
        assert str(tab.label) == "Developer [test-model]"
