import pytest
from textual.widgets import TextArea
from simple_agent.infrastructure.textual.widgets.smart_input import SubmittableTextArea

# Mock Path Factory to simulate file system
class MockPathFactory:
    def __init__(self, path_str):
        self.path_str = path_str
        self._files = {
            "test_file.txt": "Secret content",
            "another_file.md": "# Another file\nContent here"
        }

    def exists(self):
        return self.path_str in self._files

    def is_file(self):
        return True

    def read_text(self, encoding="utf-8"):
        return self._files.get(self.path_str, "")

    def __str__(self):
        return self.path_str

@pytest.mark.asyncio
async def test_submit_input_includes_referenced_files(textual_harness, monkeypatch):
    """
    Characterization test: verifies that file contents are appended to the submission
    when referenced files are present in the input.
    """
    _, _, user_input, app = textual_harness

    # Mock Path in textual_app module where it is used
    monkeypatch.setattr("simple_agent.infrastructure.textual.textual_app.Path", MockPathFactory)

    async with app.run_test() as pilot:
        await pilot.pause()
        # Note: we use query_one with the exact class or id
        text_area = app.query_one("#user-input", SubmittableTextArea)

        # 1. Simulate user selecting a file (programmatically adding to referenced set)
        # In the real app, this happens via autocomplete selection.
        text_area._referenced_files.add("test_file.txt")

        # 2. User types text including the file marker
        text_area.text = "Check this [📦test_file.txt]"

        # 3. Submit
        app.action_submit_input()
        await pilot.pause()

        # 4. Verify submission
        assert len(user_input.submissions) == 1
        submission = user_input.submissions[0]

        expected_context = '<file_context path="test_file.txt">\nSecret content\n</file_context>'

        assert "Check this [📦test_file.txt]" in submission
        assert expected_context in submission

        # Verify references are cleared
        assert len(text_area._referenced_files) == 0
        assert text_area.text == ""

@pytest.mark.asyncio
async def test_submit_input_ignores_unreferenced_files(textual_harness, monkeypatch):
    """
    Characterization test: verifies that if a file is in _referenced_files but NOT in the text
    (e.g. user deleted the marker), it is not included.
    """
    _, _, user_input, app = textual_harness
    monkeypatch.setattr("simple_agent.infrastructure.textual.textual_app.Path", MockPathFactory)

    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.query_one("#user-input", SubmittableTextArea)

        # Add file to referenced set but don't include marker in text
        text_area._referenced_files.add("test_file.txt")
        text_area.text = "Just text without file"

        app.action_submit_input()
        await pilot.pause()

        submission = user_input.submissions[0]
        assert "Just text without file" in submission
        assert "<file_context" not in submission

        # It should NOT clear references? Or should it?
        # The code clears references *if* there were referenced files used.
        # But here referenced_files = get_referenced_files() would be empty.
        # So the block `if referenced_files:` is skipped.
        # So `text_area._referenced_files.clear()` is NOT called inside that block.
        # But `text_area.clear()` IS called at the end.
        # Does `text_area.clear()` clear `_referenced_files`? No, it clears text.

        # Let's check the implementation of action_submit_input again.
        # if referenced_files:
        #    ...
        #    text_area._referenced_files.clear()

        # So if no files were found in text, the set is not cleared.
        # This seems like a potential bug or feature (memory of unused refs).
        # But let's verify current behavior.
        assert "test_file.txt" in text_area._referenced_files
