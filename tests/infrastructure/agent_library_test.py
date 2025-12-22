from simple_agent.application.agent_type import AgentType
import pytest

from simple_agent.infrastructure.agent_library import (
    BuiltinAgentLibrary,
    FileSystemAgentLibrary,
    create_agent_library,
)
from simple_agent.infrastructure.user_configuration import UserConfiguration


def test_create_agent_library(tmp_path):
    project_agents_dir = tmp_path / '.simple-agent' / 'agents'
    project_agents_dir.mkdir(parents=True, exist_ok=True)

    (project_agents_dir / 'test.agent.md').write_text(
        "---\n"
        "name: ProjectLocal\n"
        "tools: bash\n"
        "---\n"
        "This is a project-local agent.",
        encoding='utf-8'
    )

    user_config = UserConfiguration({"agents": {"start": "test"}}, str(tmp_path))

    agents = create_agent_library(user_config)
    prompt = agents._starting_agent_definition().prompt()
    assert prompt.agent_name == 'ProjectLocal'
    assert 'project-local agent' in prompt.template


def test_falls_back_to_builtin_when_no_filesystem_agents(tmp_path):
    user_config = UserConfiguration({}, str(tmp_path))

    agents = create_agent_library(user_config)
    definition = agents.read_agent_definition(AgentType('coding'))
    prompt = definition.prompt()
    assert prompt.agent_name == 'Coding'
    assert len(definition.tool_keys()) > 0


def test_load_agent_prompt_handles_missing_custom_definition_by_using_builtin(tmp_path):
    user_config = UserConfiguration({}, str(tmp_path))

    agents = create_agent_library(user_config)
    prompt = agents.read_agent_definition(AgentType('orchestrator')).prompt()
    assert prompt.agent_name == 'Orchestrator'


def test_load_agent_prompt_prefers_filesystem_directory(tmp_path):
    configured_dir = tmp_path / "agents"
    configured_dir.mkdir()
    (configured_dir / "custom.agent.md").write_text(
        "---\n"
        "name: Configured\n"
        "tools: bash\n"
        "---\n"
        "Configured definitions.",
        encoding='utf-8'
    )

    user_config = UserConfiguration(
        {"agents": {"path": str(configured_dir), "start": "custom"}},
        str(tmp_path)
    )

    agents = create_agent_library(user_config)
    prompt = agents.read_agent_definition(AgentType('custom')).prompt()
    assert prompt.agent_name == 'Configured'
    assert 'Configured definitions' in prompt.template


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
