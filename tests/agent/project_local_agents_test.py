from simple_agent.application.agent_type import AgentType
from simple_agent.infrastructure.agent_library import (
    FileSystemAgentLibrary,
    create_agent_library_old, create_agent_library,
)

def test_local_agents_given(tmp_path):
    project_agents_dir = tmp_path / '.simple-agent' / 'agents'
    project_agents_dir.mkdir(parents=True, exist_ok=True)

    (project_agents_dir / 'test.agent.md').write_text("""---
name: ProjectLocal
tools: bash
---
This is a project-local agent.""", encoding='utf-8')

    agents = create_agent_library([project_agents_dir])
    prompt = agents.read_agent_definition(AgentType('test')).prompt()
    assert prompt.agent_name == 'ProjectLocal'
    assert 'project-local agent' in prompt.template


def test_default_directory_falls_back_to_builtin_when_empty(tmp_path):
    agents = create_agent_library_old(agents_path=None, cwd=str(tmp_path))
    definition = agents.read_agent_definition(AgentType('coding'))
    prompt = definition.prompt()
    assert prompt.agent_name == 'Coding'
    assert len(definition.tool_keys()) > 0


def test_load_agent_prompt_handles_missing_custom_definition_by_using_builtin(tmp_path):
    agents = create_agent_library_old(agents_path=None, cwd=str(tmp_path))
    prompt = agents.read_agent_definition(AgentType('orchestrator')).prompt()
    assert prompt.agent_name == 'Orchestrator'


def test_load_agent_prompt_prefers_configured_directory(tmp_path):
    configured_dir = tmp_path / "agents"
    configured_dir.mkdir()
    (configured_dir / "custom.agent.md").write_text("""---
name: Configured
tools: bash
---
Configured definitions.""", encoding='utf-8')

    agents = create_agent_library_old(
        agents_path=str(configured_dir),
        cwd=str(tmp_path),
    )
    prompt = agents.read_agent_definition(AgentType('custom')).prompt()
    assert prompt.agent_name == 'Configured'
    assert 'Configured definitions' in prompt.template


def test_agent_type_discovery_uses_injected_definitions(tmp_path):
    custom_dir = tmp_path / "agents"
    custom_dir.mkdir()
    (custom_dir / "alpha.agent.md").write_text("alpha", encoding='utf-8')
    (custom_dir / "omega.agent.md").write_text("omega", encoding='utf-8')

    agent_library = FileSystemAgentLibrary(str(custom_dir))
    assert agent_library.list_agent_types() == ['alpha', 'omega']


def test_agent_definitions_support_relative_configured_path(tmp_path):
    agents_dir = tmp_path / "custom_agents"
    agents_dir.mkdir()
    (agents_dir / "via_config.agent.md").write_text("""---
name: ConfigFile
tools: bash
---
Config driven definition.""", encoding='utf-8')

    agents = create_agent_library_old(agents_path="custom_agents", cwd=str(tmp_path))
    prompt = agents.read_agent_definition(AgentType('via_config')).prompt()
    assert prompt.agent_name == 'ConfigFile'
