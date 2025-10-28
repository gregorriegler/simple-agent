from unittest.mock import patch

from approvaltests import verify

from simple_agent.infrastructure.system_prompt.agent_definition import (
    extract_tool_keys,
    load_agent_prompt
)
from simple_agent.application.system_prompt import AgentPrompt
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.infrastructure.file_system_agent_type_discovery import FileSystemAgentTypeDiscovery
from tests.test_helpers import create_all_tools_for_test


def test_generate_orchestrator_agent_system_prompt():
    tool_library = create_all_tools_for_test()
    verify_system_prompt("orchestrator", tool_library)


def test_generate_coding_system_prompt():
    tool_library = create_all_tools_for_test()
    verify_system_prompt("coding", tool_library)


def verify_system_prompt(system_prompt_md, tool_library):
    with patch('simple_agent.infrastructure.system_prompt.agent_definition._read_agents_content') as mock_agents:
        mock_agents.return_value = "# Test AGENTS.md content\nThis is a stub for testing."
        agent_type_discovery = FileSystemAgentTypeDiscovery()
        tools_documentation = generate_tools_documentation(tool_library.tools, agent_type_discovery)
        prompt = load_agent_prompt(system_prompt_md)
        system_prompt = prompt.render(tools_documentation)
        verify(system_prompt)


def test_extract_tool_keys_from_prompt():
    prompt_with_keys = """---
name: Sample Agent
tools: write_todos,ls,cat
---

# Role
Content here"""

    with patch('simple_agent.infrastructure.system_prompt.agent_definition._load_agent_definitions_file') as loader:
        loader.return_value = prompt_with_keys
        result = extract_tool_keys('sample')
    assert result == ['write_todos', 'ls', 'cat']

    prompt_with_list = """---
name: Sample List Agent
tools:
- bash
- cat
---

# Role
Content here"""

    with patch('simple_agent.infrastructure.system_prompt.agent_definition._load_agent_definitions_file') as loader:
        loader.return_value = prompt_with_list
        result = extract_tool_keys('list-sample')
    assert result == ['bash', 'cat']

    prompt_without_keys = """---
description: Sample agent
---

# Role
Content here"""

    with patch('simple_agent.infrastructure.system_prompt.agent_definition._load_agent_definitions_file') as loader:
        loader.return_value = prompt_without_keys
        result = extract_tool_keys('no-keys')
    assert result == []

    prompt_no_separator = """# Role
Content here"""

    with patch('simple_agent.infrastructure.system_prompt.agent_definition._load_agent_definitions_file') as loader:
        loader.return_value = prompt_no_separator
        result = extract_tool_keys('no-separator')
    assert result == []


def test_render_inserts_agents_content_with_placeholder():
    prompt = AgentPrompt(
        name="Test",
        template="Header\n{{AGENTS.MD}}\n{{DYNAMIC_TOOLS_PLACEHOLDER}}\nFooter",
        tool_keys=[],
        agents_content="AGENTS CONTENT"
    )

    result = prompt.render("TOOLS DOCS")

    assert result == "Header\nAGENTS CONTENT\nTOOLS DOCS\nFooter"


def test_render_removes_placeholder_when_no_agents_content():
    prompt = AgentPrompt(
        name="Test",
        template="Header\n{{AGENTS.MD}}\nFooter",
        tool_keys=[],
        agents_content=""
    )

    result = prompt.render("TOOLS DOCS")

    assert result == "Header\n\nFooter"
