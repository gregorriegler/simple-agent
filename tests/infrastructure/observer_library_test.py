import pytest

from simple_agent.infrastructure.observer_library import FileSystemObserverLibrary

NAMING_OBSERVER = """---
name: Naming
tools: [cat, bash]
---
Watch the names.
"""


@pytest.fixture
def observers_directory(tmp_path):
    (tmp_path / "naming.observer.md").write_text(NAMING_OBSERVER)
    (tmp_path / "error-handling.observer.md").write_text("---\nname: Errors\n---\n")
    (tmp_path / "coding.agent.md").write_text("---\nname: Coding\n---\n")
    return tmp_path


def test_lists_the_available_observers(observers_directory):
    library = FileSystemObserverLibrary(str(observers_directory))

    assert library.list_observers() == ["error-handling", "naming"]


def test_reads_an_observer_definition(observers_directory):
    library = FileSystemObserverLibrary(str(observers_directory))

    observer = library.read_observer_definition("naming")

    assert observer.prompt().template.strip() == "Watch the names."


def test_an_observer_may_only_read(observers_directory):
    library = FileSystemObserverLibrary(str(observers_directory))

    observer = library.read_observer_definition("naming")

    assert observer.tool_keys() == ["cat"]


def test_an_unknown_observer_is_reported(observers_directory):
    library = FileSystemObserverLibrary(str(observers_directory))

    with pytest.raises(FileNotFoundError, match="missing"):
        library.read_observer_definition("missing")
