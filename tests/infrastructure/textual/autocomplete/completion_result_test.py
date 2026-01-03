from typing import List, Tuple, Optional
from types import SimpleNamespace
from simple_agent.infrastructure.textual.autocomplete.domain import CompletionResult, FileReference, FileReferences

class FakeFileLoader:
    def __init__(self, files):
        self.files = files

    def read_file(self, path: str) -> Optional[str]:
        return self.files.get(path)

class FakeFormatter:
    def format(self, loaded_files: List[Tuple[str, str]]) -> str:
        return "\n".join([f"<{path}>{content}</{path}>" for path, content in loaded_files])

def test_expand_reads_and_formats_files():
    # Arrange
    file1 = "/path/to/test1.txt"
    file2 = "/path/to/test2.txt"

    loader = FakeFileLoader({
        file1: "Content 1",
        file2: "Content 2"
    })
    formatter = FakeFormatter()

    draft_text = f"Check [📦{file1}] and [📦{file2}]"

    files = FileReferences()
    files.add({file1, file2})

    result = CompletionResult(text=draft_text, files=files)

    # Act
    expanded_text = result.expand(loader, formatter)

    # Assert
    expected_part1 = f"<{file1}>Content 1</{file1}>"
    expected_part2 = f"<{file2}>Content 2</{file2}>"

    assert draft_text in expanded_text
    assert expected_part1 in expanded_text
    assert expected_part2 in expanded_text

def test_expand_handles_missing_files():
    # Arrange
    file_path = "/missing.txt"
    loader = FakeFileLoader({}) # Empty
    formatter = FakeFormatter()

    draft_text = f"Check [📦{file_path}]"
    files = FileReferences()
    files.add(file_path)

    result = CompletionResult(text=draft_text, files=files)

    # Act
    expanded_text = result.expand(loader, formatter)

    # Assert
    assert expanded_text == draft_text.strip()
