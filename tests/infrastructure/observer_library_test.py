import pytest

from simple_agent.infrastructure.observer_library import (
    FileSystemObserverLibrary,
    create_observer_library,
)
from simple_agent.infrastructure.user_configuration import UserConfiguration

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

    assert observer.tool_keys() == ["cat", "suggest", "complete_task"]


def test_an_unknown_observer_is_reported(observers_directory):
    library = FileSystemObserverLibrary(str(observers_directory))

    with pytest.raises(FileNotFoundError, match="missing"):
        library.read_observer_definition("missing")


def test_observers_live_next_to_the_agents(tmp_path, observers_directory):
    user_config = UserConfiguration({"agents": {"path": str(observers_directory)}})

    library = create_observer_library(user_config)

    assert library.list_observers() == ["error-handling", "naming"]


def test_the_builtin_observers_are_found_without_configuration(tmp_path):
    user_config = UserConfiguration({}, str(tmp_path))

    library = create_observer_library(user_config)

    assert "naming" in library.list_observers()


def test_the_approval_test_reviewer_is_a_builtin_observer(tmp_path):
    user_config = UserConfiguration({}, str(tmp_path))

    library = create_observer_library(user_config)

    assert "approval-test-reviewer" in library.list_observers()
