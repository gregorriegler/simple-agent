import pytest
from simple_agent.infrastructure.textual.smart_input import SmartInput

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
        text_area = app.query_one("#user-input", SmartInput)

        # 1. User types text including the file marker
        text_area.text = f"Check this [📦{test_file_path}]"

        # 2. Submit
        app.action_submit_input()
        await pilot.pause()

        # 3. Verify submission
        assert len(user_input.submissions) == 1
        submission = user_input.submissions[0]

        expected_context = f'<file_context path="{test_file_path}">\nSecret content\n</file_context>'

        assert f"Check this [📦{test_file_path}]" in submission
        assert expected_context in submission

        # Verify references are cleared
        assert len(text_area.get_referenced_files()) == 0
        assert text_area.text == ""

@pytest.mark.asyncio
async def test_submit_input_ignores_unreferenced_files(textual_harness, tmp_path):
    """
    Characterization test: verifies that if a file is not in text, it is not included.
    (This test used to check manual references, now it checks that logic doesn't hallucinate)
    """
    _, _, user_input, app = textual_harness

    # Create a dummy file path
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Secret content", encoding="utf-8")

    async with app.run_test() as pilot:
        await pilot.pause()
        text_area = app.query_one("#user-input", SmartInput)

        text_area.text = "Just text without file"

        app.action_submit_input()
        await pilot.pause()

        submission = user_input.submissions[0]
        assert "Just text without file" in submission
        assert "<file_context" not in submission

        # References should be cleared on submit
        assert len(text_area.get_referenced_files()) == 0
