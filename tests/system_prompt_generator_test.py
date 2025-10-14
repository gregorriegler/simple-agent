from approvaltests import verify
from unittest.mock import patch

from simple_agent.system_prompt_generator import generate_system_prompt, generate_tools_content
from tests.test_helpers import create_all_tools_for_test


def test_generate_tools_content_only():
    tool_library = create_all_tools_for_test()
    tools_content = generate_tools_content(tool_library)

    verify(tools_content)

def test_generate_orchestrator_agent_system_prompt():
    tool_library = create_all_tools_for_test()
    system_prompt = generate_system_prompt("orchestrator.md", tool_library)
    verify(system_prompt)


def test_generate_complete_system_prompt():
    tool_library = create_all_tools_for_test()

    with patch('simple_agent.system_prompt_generator._read_agents_content') as mock_agents:
        mock_agents.return_value = "# Test AGENTS.md content\nThis is a stub for testing."
        system_prompt = generate_system_prompt('system-prompt.md', tool_library)

    verify(system_prompt)
