import pytest
import io
import asyncio
from pathlib import Path
from rich.console import Console
from textual.widgets import TextArea, Static, Collapsible, Markdown
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentStartedEvent,
    AssistantSaidEvent,
    ErrorEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    ToolCalledEvent,
    ToolCancelledEvent,
    ToolResultEvent,
)
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from approvaltests import verify

# Helper to dump UI state (copied from textual_ui_golden_test.py)
def dump_ui_state(app: TextualApp) -> str:
    lines = []

    # Dump Tabs
    tabs = app.query("TabPane")
    lines.append(f"Tabs: {[t.id for t in tabs]}")
    lines.append(f"Active Tab: {app.query_one('TabbedContent').active}")

    # Dump Visible Widgets in Main Content
    for widget in app.screen.walk_children():
        indent = "  " * len(list(widget.ancestors))
        classes = sorted(list(widget.classes))
        info = f"{indent}{widget.__class__.__name__} id='{widget.id}' classes='{' '.join(classes)}'"

        if isinstance(widget, Markdown):
             info += f" source={repr(widget.source[:50])}..."

        if isinstance(widget, TextArea):
            info += f" text={repr(widget.text)}"

        if isinstance(widget, Collapsible):
            info += f" title={repr(widget.title)} collapsed={widget.collapsed}"

        if isinstance(widget, Static) and not isinstance(widget, (Markdown, TextArea)):
             if hasattr(widget, "renderable") and hasattr(widget.renderable, "plain"):
                 info += f" content={repr(widget.renderable.plain)}"

        lines.append(info)

    return "\n".join(lines)

def dump_ascii_screen(app: TextualApp) -> str:
    console = Console(
        record=True,
        width=app.size.width,
        height=app.size.height,
        force_terminal=False,
        file=io.StringIO(),
        color_system=None,
        legacy_windows=False,
        safe_box=False,
    )
    console.print(app.screen._compositor)
    output = console.export_text()
    return "\n".join(line.rstrip() for line in output.splitlines())

class MockUserInput:
    def __init__(self):
        self.submitted_content = []

    def submit_input(self, content: str):
        self.submitted_content.append(content)

    def close(self):
        pass

@pytest.mark.asyncio
async def test_golden_complex_scenarios(tmp_path):
    """
    Test complex UI scenarios:
    1. Subagents (tabs)
    2. Session Lifecycle (Interrupted, Error)
    3. Tool Call Variants (Cancelled, Diff, Suppressed)
    4. File Context Submission
    """
    agent_id = AgentId("Agent")
    mock_user_input = MockUserInput()
    app = TextualApp(user_input=mock_user_input, root_agent_id=agent_id)

    # Disable loading timer
    app.set_interval = lambda *args, **kwargs: None

    timeline = []

    def capture_step(step_name: str):
        timeline.append(f"--- Step: {step_name} (Widget Tree) ---")
        timeline.append(dump_ui_state(app))
        timeline.append("")
        timeline.append(f"--- Step: {step_name} (ASCII UI) ---")
        timeline.append(dump_ascii_screen(app))
        timeline.append("")

    # Create a dummy file for file context test
    dummy_file = tmp_path / "test_context.txt"
    dummy_file.write_text("This is file content.", encoding="utf-8")

    async with app.run_test(size=(80, 24)) as pilot:
        capture_step("Initial State")

        # --- Scenario: Subagents ---
        sub_agent_id = AgentId("SubAgent")
        app.on_domain_event_message(DomainEventMessage(AgentStartedEvent(sub_agent_id, "SubAgent", "gpt-4")))
        await pilot.pause()
        capture_step("SubAgent Started")

        app.on_domain_event_message(DomainEventMessage(AssistantSaidEvent(sub_agent_id, "Hello from SubAgent")))
        await pilot.pause()
        capture_step("SubAgent Spoke")

        app.on_domain_event_message(DomainEventMessage(SessionEndedEvent(sub_agent_id)))
        await pilot.pause()
        capture_step("SubAgent Ended")

        # --- Scenario: Lifecycle & Errors ---
        app.on_domain_event_message(DomainEventMessage(ErrorEvent(agent_id, "Something went wrong")))
        await pilot.pause()
        capture_step("Error Event")

        app.on_domain_event_message(DomainEventMessage(SessionInterruptedEvent(agent_id)))
        await pilot.pause()
        capture_step("Session Interrupted")

        # --- Scenario: Tool Call Variants ---

        # 1. Suppressed Tool Call (write-todos)
        call_id_todo = "call-todo"
        app.on_domain_event_message(DomainEventMessage(ToolCalledEvent(agent_id, call_id_todo, type("Tool", (), {"header": lambda s: "write_todos()"})())))
        await pilot.pause()
        capture_step("Tool Call (Suppressed)")

        # 2. Diff Result
        call_id_diff = "call-diff"
        app.on_domain_event_message(DomainEventMessage(ToolCalledEvent(agent_id, call_id_diff, type("Tool", (), {"header": lambda s: "apply_diff()"})())))
        await pilot.pause()

        diff_content = """<<<<<<< SEARCH
old line
=======
new line
>>>>>>> REPLACE"""
        result_diff = SingleToolResult(
            message=diff_content,
            display_language="diff",
            status=ToolResultStatus.SUCCESS
        )
        app.on_domain_event_message(DomainEventMessage(ToolResultEvent(agent_id, call_id_diff, result_diff)))
        await pilot.pause()
        capture_step("Tool Result (Diff)")

        # 3. Cancelled Tool
        call_id_cancel = "call-cancel"
        app.on_domain_event_message(DomainEventMessage(ToolCalledEvent(agent_id, call_id_cancel, type("Tool", (), {"header": lambda s: "long_running()"})())))
        await pilot.pause()

        app.on_domain_event_message(DomainEventMessage(ToolCancelledEvent(agent_id, call_id_cancel)))
        await pilot.pause()
        capture_step("Tool Cancelled")

        # --- Scenario: File Context Submission ---
        # We simulate typing a file reference.
        text_area = app.query_one("#user-input", TextArea)

        file_path_str = str(dummy_file.absolute())
        marker = f"[📦{file_path_str}]"
        text_area.text = f"Look at this file: {marker}"
        text_area._referenced_files.add(file_path_str)

        await pilot.press("enter")
        await pilot.pause()
        capture_step("File Context Submitted")

        # Verify Mock Input
        assert len(mock_user_input.submitted_content) == 1
        submitted = mock_user_input.submitted_content[0]
        assert "Look at this file: " in submitted
        assert f'<file_context path="{file_path_str}">' in submitted
        assert "This is file content." in submitted

        # Verify timeline
        verify("\n".join(timeline))
