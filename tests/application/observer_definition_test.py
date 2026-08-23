from simple_agent.application.observer_definition import ObserverDefinition

from simple_agent.application.agent_type import AgentType
from tests.system_prompt_generator_test import GroundRulesStub


def observer_with_tools(tools):
    content = f"---\nname: Naming\ntools: {tools}\n---\nWatch the names.\n"
    return ObserverDefinition(AgentType("naming"), content, GroundRulesStub())


def test_read_only_tools_are_kept():
    assert observer_with_tools("[ls, cat]").tool_keys() == ["ls", "cat"]


def test_writing_tools_are_stripped():
    observer = observer_with_tools("[cat, create_file, replace_file_content, bash]")

    assert observer.tool_keys() == ["cat"]


def test_an_observer_without_tools_can_still_read():
    assert observer_with_tools("[]").tool_keys() == ["ls", "cat"]
