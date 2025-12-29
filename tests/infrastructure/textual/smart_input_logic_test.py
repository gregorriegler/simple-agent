import pytest
from textual.widgets import TextArea
from simple_agent.infrastructure.textual.widgets.smart_input import SubmittableTextArea

@pytest.mark.asyncio
async def test_submit_input_includes_referenced_files(textual_harness, tmp_path):
    """
    Characterization test: verifies that file contents are appended to the submission
    when referenced files are present in the input.
    """
    _, _, user_input, app = textual_harness

    # Create a real temporary file
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Secret content", encoding="utf-8")
    test_file_path = str(test_file)

    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.query_one("#user-input", SubmittableTextArea)

        # 1. Simulate user selecting a file (programmatically adding to referenced set)
        text_area._referenced_files.add(test_file_path)

        # 2. User types text including the file marker
        text_area.text = f"Check this [📦{test_file_path}]"

        # 3. Submit
        app.action_submit_input()
        await pilot.pause()

        # 4. Verify submission
        assert len(user_input.submissions) == 1
        submission = user_input.submissions[0]

        expected_context = f'<file_context path="{test_file_path}">\nSecret content\n</file_context>'

        assert f"Check this [📦{test_file_path}]" in submission
        assert expected_context in submission

        # Verify references are cleared
        assert len(text_area._referenced_files) == 0
        assert text_area.text == ""

@pytest.mark.asyncio
async def test_submit_input_ignores_unreferenced_files(textual_harness, tmp_path):
    """
    Characterization test: verifies that if a file is in _referenced_files but NOT in the text
    (e.g. user deleted the marker), it is not included.
    """
    _, _, user_input, app = textual_harness

    # Create a dummy file path (file existence check happens inside logic, so we should create it to be sure logic isn't failing on exists())
    # Actually, if the logic is "ignore if not in text", it doesn't even reach file reading.
    # But let's create it to isolate the test to just "is it in text?"
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Secret content", encoding="utf-8")
    test_file_path = str(test_file)

    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.query_one("#user-input", SubmittableTextArea)

        # Add file to referenced set but don't include marker in text
        text_area._referenced_files.add(test_file_path)
        text_area.text = "Just text without file"

        app.action_submit_input()
        await pilot.pause()

        submission = user_input.submissions[0]
        assert "Just text without file" in submission
        assert "<file_context" not in submission

        # References should be cleared on submit
        assert len(text_area._referenced_files) == 0
