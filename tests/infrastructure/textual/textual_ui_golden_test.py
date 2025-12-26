import pytest
import asyncio
from textual.widgets import TextArea, Static, Collapsible, Markdown
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    SessionStartedEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
    AssistantSaidEvent,
    ToolCalledEvent,
    ToolResultEvent,
)
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from approvaltests import verify, Options
from approvaltests.reporters import GenericDiffReporterFactory


# Helper to dump UI state
def dump_ui_state(app: TextualApp) -> str:
    lines = []

    # Dump Tabs
    tabs = app.query("TabPane")
    lines.append(f"Tabs: {[t.id for t in tabs]}")
    lines.append(f"Active Tab: {app.query_one('TabbedContent').active}")

    # Dump Visible Widgets in Main Content
    # We walk the tree and print relevant info
    for widget in app.screen.walk_children():
        # Skip some containers if they are just layout
        indent = "  " * len(list(widget.ancestors))
        classes = sorted(list(widget.classes))
        info = f"{indent}{widget.__class__.__name__} id='{widget.id}' classes='{' '.join(classes)}'"

        # Add specific state
        if isinstance(widget, Markdown):
             # Markdown content isn't easily accessible as raw text directly from widget.source
             # but we can try accessing the source if available
             # In Textual, Markdown.source is the source text
             info += f" source={repr(widget.source[:50])}..."

        if isinstance(widget, TextArea):
            info += f" text={repr(widget.text)}"

        if isinstance(widget, Collapsible):
            info += f" title={repr(widget.title)} collapsed={widget.collapsed}"

        if isinstance(widget, Static) and not isinstance(widget, (Markdown, TextArea)):
             # Try to get text from renderable if it's simple
             if hasattr(widget, "renderable") and hasattr(widget.renderable, "plain"):
                 info += f" content={repr(widget.renderable.plain)}"

        lines.append(info)

    return "\n".join(lines)

@pytest.mark.asyncio
async def test_golden_happy_path_flow():
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
    agent_id = AgentId("Agent")
    app = TextualApp(user_input=None, root_agent_id=agent_id)

    # Disable loading timer to avoid non-determinism
    # We can mock set_interval on the app or just ensure we don't wait for it
    # But better to prevent it from updating state asynchronously
    app.set_interval = lambda *args, **kwargs: None

    timeline = []

    def capture_step(step_name: str):
        dump = dump_ui_state(app)
        timeline.append(f"--- Step: {step_name} ---")
        timeline.append(dump)
        timeline.append("\n")

    async with app.run_test(size=(80, 24)) as pilot:
        # 1. Session Start (Initial state)
        # Note: In a real run, the session might start automatically or via an event.
        # We inject the event to simulate the backend starting the session.
        app.on_domain_event_message(DomainEventMessage(SessionStartedEvent(agent_id, False)))
        await pilot.pause()
        capture_step("Session Started")

        # 2. User Prompt Requested
        app.on_domain_event_message(DomainEventMessage(UserPromptRequestedEvent(agent_id)))
        await pilot.pause()
        capture_step("User Prompt Requested")

        # 3. User prompts "Hello"
        # Drive the UI properly: Focus input, Type "Hello", Press Enter
        await pilot.click("#user-input")
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
        app.on_domain_event_message(DomainEventMessage(UserPromptedEvent(agent_id, "Hello")))
        app.on_domain_event_message(DomainEventMessage(AssistantSaidEvent(agent_id, "Hi there!")))
        await pilot.pause()
        capture_step("Assistant Reply")

        # 5. Assistant Calls Tool
        call_id = "call-1"
        tool_header = "search_files(query='test')"
        app.on_domain_event_message(DomainEventMessage(ToolCalledEvent(agent_id, call_id, type("Tool", (), {"header": lambda s: tool_header})())))
        await pilot.pause()
        capture_step("Tool Called")

        # 6. Tool Returns Result
        result = SingleToolResult(message="Found 1 file.", display_title="Search Results")
        app.on_domain_event_message(DomainEventMessage(ToolResultEvent(agent_id, call_id, result)))
        await pilot.pause()
        capture_step("Tool Result")

        # Verify Timeline
        verify("\n".join(timeline))
