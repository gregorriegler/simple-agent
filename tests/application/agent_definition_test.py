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

    assert agent_definition.agent_name() == "helper"
    assert prompt_first.agent_name == "helper"
    assert prompt_first.template == "You are a helper.\n"
    assert prompt_first.agents_content == "shared ground rules"
    assert agent_definition.tool_keys() == ["hammer", "saw"]
    assert prompt_second is prompt_first, "prompt should be cached"
    assert ground_rules.calls == 1


def test_model_and_prompt_share_cached_load():
    content = """---
name: helper
model: gpt-4
---
You are a helper."""
    agent_definition = AgentDefinition(
        AgentType("assistant"), content, StubGroundRules("rules")
    )

    assert agent_definition.model() == "gpt-4"
    assert agent_definition.prompt().agent_name == "helper"


def test_no_front_matter():
    content = "No front matter here"
    agent_definition = AgentDefinition(
        AgentType("assistant"), content, StubGroundRules("rules")
    )

    assert agent_definition.model() is None
    assert agent_definition.tool_keys() == []
    assert agent_definition.prompt().template == content


def test_empty_content():
    content = ""
    agent_definition = AgentDefinition(
        AgentType("assistant"), content, StubGroundRules("rules")
    )

    assert agent_definition.model() is None
    assert agent_definition.prompt().agent_name == "Assistant"


def test_front_matter_with_windows_line_endings():
    content = "---\r\nname: windows\r\nmodel: gpt-4\r\n---\r\nTemplate body"
    agent_definition = AgentDefinition(
        AgentType("assistant"), content, StubGroundRules("rules")
    )

    assert agent_definition.model() == "gpt-4"
    assert agent_definition.agent_name() == "windows"
    assert agent_definition.prompt().template == "Template body"


def test_incomplete_front_matter():
    content = "---\nname: incomplete\nNo closing marker"
    agent_definition = AgentDefinition(
        AgentType("assistant"), content, StubGroundRules("rules")
    )

    assert agent_definition.model() is None
    assert agent_definition.prompt().template == content


def test_invalid_yaml_front_matter():
    content = "---\nvalid: yaml: :\n---\nBody"
    agent_definition = AgentDefinition(
        AgentType("assistant"), content, StubGroundRules("rules")
    )

    assert agent_definition.model() is None
    assert agent_definition.prompt().template == "Body"


def test_front_matter_not_a_dict():
    content = "---\n- item1\n- item2\n---\nBody"
    agent_definition = AgentDefinition(
        AgentType("assistant"), content, StubGroundRules("rules")
    )

    assert agent_definition.model() is None
    assert agent_definition.prompt().template == "Body"


def test_tool_keys_parsing():
    # String input
    agent1 = AgentDefinition(
        AgentType("a"), "---\ntools: hammer, saw\n---\n", StubGroundRules("")
    )
    assert agent1.tool_keys() == ["hammer", "saw"]

    # List input with empty/whitespace
    agent2 = AgentDefinition(
        AgentType("a"),
        '---\ntools: [" alpha", "", "beta "]\n---\n',
        StubGroundRules(""),
    )
    assert agent2.tool_keys() == ["alpha", "beta"]

    # Invalid type
    agent3 = AgentDefinition(
        AgentType("a"), "---\ntools: 123\n---\n", StubGroundRules("")
    )
    assert agent3.tool_keys() == []


def test_parse_front_matter_invalid_newline_after_triple_dash():
    content = "---no-newline\nname: test\n---\nBody"
    agent_definition = AgentDefinition(
        AgentType("assistant"), content, StubGroundRules("rules")
    )
    assert agent_definition.model() is None
    assert agent_definition.prompt().template == content


def test_parse_front_matter_with_prefix():
    content = "  ---\nname: prefixed\n---\nBody"
    agent_definition = AgentDefinition(
        AgentType("assistant"), content, StubGroundRules("rules")
    )
    assert agent_definition.agent_name() == "prefixed"
    assert agent_definition.prompt().template == "  Body"
