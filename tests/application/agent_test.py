import pytest

from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId
from simple_agent.application.brain import Brain
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import Messages
from simple_agent.application.user_input import DummyUserInput
from tests.agent.agent_interrupts_immediately_test import EmptyToolLibrary
from tests.application.model_switching_test import MockLLMProvider


@pytest.mark.asyncio
async def test_agent_runtime_switch_updates_brain_configuration():
    provider = MockLLMProvider()
    old_tools = EmptyToolLibrary()
    new_tools = EmptyToolLibrary()
    context = Messages(system_prompt="old system prompt")
    context.user_says("Keep this history")
    agent = Agent(
        agent_id=AgentId("Agent"),
        agent_name="Old Agent",
        tools=old_tools,
        llm_provider=provider,
        model_name="default-model",
        user_input=Input(DummyUserInput()),
        event_bus=SimpleEventBus(),
        context=context,
    )

    new_brain = Brain(
        name="New Agent",
        system_prompt="new system prompt",
        tools=new_tools,
        model_name="new-model",
    )

    agent.update_brain(new_brain)

    assert agent.agent_name == "New Agent"
    assert agent.llm.model == "new-model"
    assert agent.tools is new_tools
    actual = agent.context.to_list()
    expected = [
        {"role": "system", "content": "new system prompt"},
        {"role": "user", "content": "Keep this history"},
    ]
    assert actual == expected
