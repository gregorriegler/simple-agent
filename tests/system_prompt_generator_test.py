from approvaltests import verify

from simple_agent.system_prompt_generator import SystemPromptGenerator


def test_generate_tools_content_only():
    generator = SystemPromptGenerator()
    tools_content = generator._generate_tools_content()

    verify(tools_content)
