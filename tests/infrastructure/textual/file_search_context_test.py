import pytest
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.smart_input import SmartInput
from simple_agent.application.events import UserPromptedEvent
from simple_agent.application.agent_id import AgentId

class StubUserInput:
    def __init__(self) -> None:
        self.inputs = []

    def submit_input(self, content: str) -> None:
        self.inputs.append(content)

    def close(self) -> None:
        pass

    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

@pytest.mark.asyncio
async def test_submit_includes_referenced_file_content(tmp_path):
    # Setup a dummy file
    dummy_file = tmp_path / "test_file.txt"
    dummy_file.write_text("Hello World", encoding="utf-8")
    
    user_input = StubUserInput()
    app = TextualApp(user_input)

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)
        
        # Simulate typing and selecting file
        file_path_str = str(dummy_file)
        text_area.text = f"Check this [📦{file_path_str}]"
        
        # Action
        app.action_submit_input()
        await pilot.pause()
        
        # Assert
        assert len(user_input.inputs) == 1
        submitted_text = user_input.inputs[0]
        
        assert f"Check this [📦{file_path_str}]" in submitted_text
        assert f'<file_context path="{file_path_str}">' in submitted_text
        assert "Hello World" in submitted_text
        assert "</file_context>" in submitted_text
        
        # Verify references are cleared
        assert len(text_area.get_referenced_files()) == 0

@pytest.mark.asyncio
async def test_submit_ignores_removed_file_references(tmp_path):
    # Setup a dummy file
    dummy_file = tmp_path / "test_file.txt"
    dummy_file.write_text("Should Not Appear", encoding="utf-8")
    
    user_input = StubUserInput()
    app = TextualApp(user_input)

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)
        
        # Simulate selecting file but then deleting it from text
        file_path_str = str(dummy_file)
        text_area.text = "I deleted the file ref"
        
        # Action
        app.action_submit_input()
        await pilot.pause()
        
        # Assert
        assert len(user_input.inputs) == 1
        submitted_text = user_input.inputs[0]
        
        assert "I deleted the file ref" in submitted_text
        assert "Should Not Appear" not in submitted_text

@pytest.mark.asyncio
async def test_submit_ignores_corrupted_marker(tmp_path):
    # Setup a dummy file
    dummy_file = tmp_path / "test_file.txt"
    dummy_file.write_text("Should Not Appear", encoding="utf-8")
    
    user_input = StubUserInput()
    app = TextualApp(user_input)

    async with app.run_test() as pilot:
        text_area = app.query_one("#user-input", SmartInput)
        
        # Simulate selecting file but then deleting the closing bracket
        file_path_str = str(dummy_file)
        # Corrupted marker
        text_area.text = f"Check this [📦{file_path_str}"
        
        # Action
        app.action_submit_input()
        await pilot.pause()
        
        # Assert
        assert len(user_input.inputs) == 1
        submitted_text = user_input.inputs[0]
        
        # The text remains as typed
        assert f"Check this [📦{file_path_str}" in submitted_text
        # But content is NOT attached
        assert "Should Not Appear" not in submitted_text
        assert "<file_context" not in submitted_text

@pytest.mark.asyncio
async def test_user_prompted_event_display_compaction():
    user_input = StubUserInput()
    app = TextualApp(user_input)
    
    async with app.run_test() as pilot:
        # Simulate UserPromptedEvent with context
        agent_id = AgentId("Agent")
        # This simulates "Check this [📦main.py]" followed by the appended context
        full_text = 'Check this [📦main.py]\n<file_context path="main.py">\nLots of content...\n</file_context>'
        event = UserPromptedEvent(agent_id=agent_id, input_text=full_text)
        
        # Trigger event handler
        app.on_domain_event_message(type("Message", (), {"event": event})())
        await pilot.pause()

        # Verify side effect on ChatLog
        # We need to find the chat log for this agent
        _, log_id, _ = app.panel_ids_for(agent_id)
        chat_log = app.query_one(f"#{log_id}-scroll")

        # Get the last markdown widget added
        from textual.widgets import Markdown
        markdowns = list(chat_log.query(Markdown))
        assert len(markdowns) > 0
        
        # Inspect the source text of the last message
        display_text = markdowns[-1]._markdown
        
        # We expect the appended block removed, and core text preserved (since it already has the marker)
        assert "**User:** Check this [📦main.py]" in display_text
        assert "Lots of content..." not in display_text
        # Ensure we don't have double nesting [📦[📦main.py]]
        assert "[📦[📦main.py]]" not in display_text