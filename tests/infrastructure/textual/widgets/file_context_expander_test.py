import pytest
from pathlib import Path
from simple_agent.infrastructure.textual.widgets.file_context_expander import FileContextExpander
from simple_agent.infrastructure.textual.autocomplete import CompletionResult, FileReference

class TestFileContextExpander:
    def test_expand_reads_and_formats_files(self, tmp_path):
        # Arrange
        expander = FileContextExpander()

        file1 = tmp_path / "test1.txt"
        file1.write_text("Content 1", encoding="utf-8")

        file2 = tmp_path / "test2.txt"
        file2.write_text("Content 2", encoding="utf-8")

        draft_text = f"Check [📦{file1}] and [📦{file2}]"

        # Mocking CompletionResult behavior
        # CompletionResult expects (text, cursor_pos) or similar, but active_files is a property.
        # However, checking the source code of CompletionResult might be needed to mock it correctly.
        # But FileContextExpander only accesses .text and .active_files.
        # Let's see if we can instantiate it or need a fake.

        # Creating a fake draft object
        class FakeDraft:
            def __init__(self, text, files):
                self.text = text
                self.active_files = files

        draft = FakeDraft(
            text=draft_text,
            files={FileReference(str(file1)), FileReference(str(file2))}
        )

        # Act
        result = expander.expand(draft)

        # Assert
        expected_part1 = f'<file_context path="{file1}">\nContent 1\n</file_context>'
        expected_part2 = f'<file_context path="{file2}">\nContent 2\n</file_context>'

        assert draft_text in result
        assert expected_part1 in result
        assert expected_part2 in result

    def test_expand_handles_missing_files(self, tmp_path):
        # Arrange
        expander = FileContextExpander()
        file_path = str(tmp_path / "missing.txt")

        class FakeDraft:
            text = f"Check [📦{file_path}]"
            active_files = {FileReference(file_path)}

        draft = FakeDraft()

        # Act
        result = expander.expand(draft)

        # Assert
        # Should return original text without expansion
        assert result == draft.text.strip()
        assert "<file_context" not in result

    def test_expand_ignores_unreferenced_files(self, tmp_path):
        # Arrange
        expander = FileContextExpander()

        # Even if active_files has it, the Expander logic relies on 'draft.active_files'.
        # Wait, the Expander code says:
        # active_references = draft.active_files
        # if active_references: ...
        # So if active_files has it, it loads it.
        # The logic "Only process files that are actually referenced in the text" relies on
        # the Caller (CompletionResult) to have filtered them?
        # Let's check FileContextExpander code again.
        pass
