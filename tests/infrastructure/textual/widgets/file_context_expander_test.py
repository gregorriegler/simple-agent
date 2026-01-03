import pytest
from pathlib import Path
from types import SimpleNamespace
from simple_agent.infrastructure.textual.widgets.file_context_expander import FileContextExpander
from simple_agent.infrastructure.textual.autocomplete import FileReference

def test_expand_reads_and_formats_files(tmp_path):
    # Arrange
    expander = FileContextExpander()

    file1 = tmp_path / "test1.txt"
    file1.write_text("Content 1", encoding="utf-8")

    file2 = tmp_path / "test2.txt"
    file2.write_text("Content 2", encoding="utf-8")

    draft_text = f"Check [📦{file1}] and [📦{file2}]"

    draft = SimpleNamespace(
        text=draft_text,
        active_files={FileReference(str(file1)), FileReference(str(file2))}
    )

    # Act
    result = expander.expand(draft)

    # Assert
    expected_part1 = f'<file_context path="{file1}">\nContent 1\n</file_context>'
    expected_part2 = f'<file_context path="{file2}">\nContent 2\n</file_context>'

    assert draft_text in result
    assert expected_part1 in result
    assert expected_part2 in result

def test_expand_handles_missing_files(tmp_path):
    # Arrange
    expander = FileContextExpander()
    file_path = str(tmp_path / "missing.txt")

    draft = SimpleNamespace(
        text=f"Check [📦{file_path}]",
        active_files={FileReference(file_path)}
    )

    # Act
    result = expander.expand(draft)

    # Assert
    # Should return original text without expansion
    assert result == draft.text.strip()
    assert "<file_context" not in result
