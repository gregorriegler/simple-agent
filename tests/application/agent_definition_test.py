from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_type import AgentType


class StubGroundRules:
    def __init__(self, content: str):
        self.content = content
        self.calls = 0

    def read(self) -> str:
        self.calls += 1
        return self.content


def test_prompt_uses_front_matter_and_caches_result():
    ground_rules = StubGroundRules("shared ground rules")
    content = """---
name: helper
tools: [hammer, saw]
---
You are a helper.
"""
    agent_definition = AgentDefinition(AgentType("assistant"), content, ground_rules)

    prompt_first = agent_definition.prompt()
    prompt_second = agent_definition.prompt()

    assert prompt_first.agent_name == "helper"
    assert prompt_first.template == "You are a helper.\n"
    assert prompt_first.agents_content == "shared ground rules"
    assert agent_definition.tool_keys() == ["hammer", "saw"]
    assert prompt_second is prompt_first, "prompt should be cached"
    assert ground_rules.calls == 1


def test_parse_front_matter_handles_prefix_and_crlf_newlines():
    content = "  ---\r\nname: windows\r\ntools: [alpha, beta]\r\n---\r\nTemplate body\nmore"
    agent_definition = AgentDefinition(AgentType("assistant"), content, StubGroundRules("rules"))

    metadata, template = agent_definition._parse_front_matter(content)

    assert metadata == {"name": "windows", "tools": ["alpha", "beta"]}
    assert template == "  Template body\nmore"


def test_parse_front_matter_without_markers_returns_original():
    content = "No front matter here"
    agent_definition = AgentDefinition(AgentType("assistant"), content, StubGroundRules("rules"))

    metadata, template = agent_definition._parse_front_matter(content)

    assert metadata == {}
    assert template == content


def test_read_tool_keys_handles_various_inputs():
    assert AgentDefinition._read_tool_keys(None) == []
    assert AgentDefinition._read_tool_keys("hammer, saw , ") == ["hammer", "saw"]
    assert AgentDefinition._read_tool_keys([" alpha", "", "beta "]) == ["alpha", "beta"]
    assert AgentDefinition._read_tool_keys(123) == []


def test_model_returns_value_from_front_matter():
    content = """---
name: helper
model: gemini-flash
---
You are a helper.
"""
    agent_definition = AgentDefinition(AgentType("assistant"), content, StubGroundRules("rules"))

    assert agent_definition.model() == "gemini-flash"


def test_model_returns_none_when_not_specified():
    content = """---
name: helper
---
You are a helper.
"""
    agent_definition = AgentDefinition(AgentType("assistant"), content, StubGroundRules("rules"))

    assert agent_definition.model() is None


def test_model_and_prompt_share_cached_load():
    content = """---
name: helper
model: gpt-4
---
You are a helper.
"""
    agent_definition = AgentDefinition(AgentType("assistant"), content, StubGroundRules("rules"))

    model = agent_definition.model()
    prompt = agent_definition.prompt()

    assert model == "gpt-4"
    assert prompt.agent_name == "helper"
