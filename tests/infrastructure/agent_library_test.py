from simple_agent.application.agent_type import AgentType
import pytest

from simple_agent.infrastructure.agent_library import (
    BuiltinAgentLibrary,
    FileSystemAgentLibrary,
    create_agent_library,
)


def test_filesystem_agent_library_lists_sorted_agent_types(tmp_path):
    (tmp_path / "b.agent.md").write_text("content", encoding="utf-8")
    (tmp_path / "a.agent.md").write_text("content", encoding="utf-8")

    library = FileSystemAgentLibrary(str(tmp_path))

    assert library.list_agent_types() == ["a", "b"]


def test_filesystem_agent_library_reads_definition(tmp_path):
    path = tmp_path / "coding.agent.md"
    path.write_text("# Agent\n", encoding="utf-8")
    library = FileSystemAgentLibrary(str(tmp_path))

    definition = library.read_agent_definition(AgentType("coding"))

    assert definition.agent_name() == "Coding"


def test_filesystem_agent_library_reports_missing_definition(tmp_path):
    library = FileSystemAgentLibrary(str(tmp_path))

    with pytest.raises(FileNotFoundError, match="not found"):
        library.read_agent_definition(AgentType("missing"))


def test_create_agent_library_prefers_filesystem_agents(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "coding.agent.md").write_text("# Agent\n", encoding="utf-8")

    library = create_agent_library("agents", str(tmp_path))

    assert isinstance(library, FileSystemAgentLibrary)


def test_builtin_agent_library_reads_from_fallback_path():
    library = BuiltinAgentLibrary()
    library.package = "missing_package"

    definition = library.read_agent_definition(AgentType("coding"))

    assert definition.agent_name() == "Coding"


def test_builtin_agent_library_discovers_agents_from_fallback():
    library = BuiltinAgentLibrary()
    library.package = "missing_package"

    agent_types = library.list_agent_types()

    assert "coding" in agent_types

