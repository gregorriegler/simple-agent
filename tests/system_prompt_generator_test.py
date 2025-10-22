from approvaltests import verify
from unittest.mock import patch

from simple_agent.system_prompt_generator import (
    extract_agent_metadata_from_prompt,
    extract_tool_keys_from_prompt,
    generate_system_prompt,
    generate_tools_content,
)
from tests.test_helpers import create_all_tools_for_test


def test_generate_tools_content_only():
    tool_library = create_all_tools_for_test()
    tools_content = generate_tools_content(tool_library)
    verify(tools_content)


def test_generate_orchestrator_agent_system_prompt():
    tool_library = create_all_tools_for_test()
    verify_system_prompt("orchestrator.agent.md", tool_library)


def test_generate_coding_system_prompt():
    tool_library = create_all_tools_for_test()
    verify_system_prompt("coding.agent.md", tool_library)


def verify_system_prompt(system_prompt_md, tool_library):
    with patch('simple_agent.system_prompt_generator._read_agents_content') as mock_agents:
        mock_agents.return_value = "# Test AGENTS.md content\nThis is a stub for testing."
        system_prompt = generate_system_prompt(system_prompt_md, tool_library)
        verify(system_prompt)


def test_extract_tool_keys_from_prompt():
    prompt_with_keys = """---
name: Sample Agent
tools: write_todos,ls,cat
---

# Role
Content here"""

    metadata = extract_agent_metadata_from_prompt(prompt_with_keys)
    assert metadata['name'] == 'Sample Agent'

    result = extract_tool_keys_from_prompt(prompt_with_keys)
    assert result == ['write_todos', 'ls', 'cat']

    prompt_with_list = """---
name: Sample List Agent
tools:
- bash
- cat
---

# Role
Content here"""

    metadata = extract_agent_metadata_from_prompt(prompt_with_list)
    assert metadata['name'] == 'Sample List Agent'

    result = extract_tool_keys_from_prompt(prompt_with_list)
    assert result == ['bash', 'cat']

    prompt_without_keys = """---
description: Sample agent
---

# Role
Content here"""

    result = extract_tool_keys_from_prompt(prompt_without_keys)
    assert result == []

    prompt_no_separator = """# Role
Content here"""

    result = extract_tool_keys_from_prompt(prompt_no_separator)
    assert result == []
