from approvaltests import verify

from simple_agent.system_prompt_generator import generate_system_prompt, _generate_tools_content
from simple_agent.tools.tool_library import AllTools


def test_generate_tools_content_only():
    tool_library = AllTools()
    tools_content = _generate_tools_content(tool_library)

    verify(tools_content)


def test_generate_complete_system_prompt():
    tool_library = AllTools()
    system_prompt = generate_system_prompt(tool_library)

    verify(system_prompt)
