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
from tests.infrastructure.textual.test_utils import dump_ui_state, dump_ascii_screen, MockUserInput
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog

@pytest.mark.asyncio
async def test_golden_complex_scenarios(tmp_path, monkeypatch):
    """
    Test complex UI scenarios:
    1. Subagents (tabs)
    2. Session Lifecycle (Interrupted, Error)
    3. Tool Call Variants (Cancelled, Diff, Suppressed)
    4. File Context Submission
    """
    # Disable timers on ToolLog to prevent non-deterministic loading animations
    monkeypatch.setattr(ToolLog, "set_interval", lambda *args, **kwargs: None)

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

    # Mock Path to ensure deterministic file paths in output
    class MockPath:
        def __init__(self, path_str):
            self.path_str = str(path_str)

        def exists(self):
            return True

        def is_file(self):
            return True

        def read_text(self, encoding="utf-8"):
            return "This is file content."

        def __str__(self):
            return self.path_str

    monkeypatch.setattr("simple_agent.infrastructure.textual.textual_app.Path", MockPath)

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

        # Wait for the tool call to be rendered
        await pilot.pause()

        app.on_domain_event_message(DomainEventMessage(ToolCancelledEvent(agent_id, call_id_cancel)))
        await pilot.pause()

        # Verification: Wait for UI update
        # We need to ensure the Collapsible title has updated to include "(Cancelled)"
        # This might take a cycle.
        async def wait_for_cancel():
            for _ in range(10):
                await pilot.pause(0.1)
                # Check directly in the app widget tree
                try:
                    # Find the collapsible for the cancelled tool
                    # We iterate over collapsibles to find the one with the title
                    for widget in app.query(Collapsible):
                         if "long_running()" in str(widget.title) and "(Cancelled)" in str(widget.title):
                             return
                except Exception:
                    pass

        await wait_for_cancel()
        capture_step("Tool Cancelled")

        # --- Scenario: File Context Submission ---
        # We simulate typing a file reference using a fixed path
        text_area = app.query_one("#user-input", TextArea)

        file_path_str = "/mock/context.txt"
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
