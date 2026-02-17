import pytest

from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId
from simple_agent.application.brain import Brain
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import AgentChangedEvent, ModelChangedEvent
from simple_agent.application.input import Input
from simple_agent.application.llm import Messages
from simple_agent.application.user_input import DummyUserInput
from tests.agent.agent_interrupts_immediately_test import EmptyToolLibrary
from tests.application.model_switching_test import MockLLMProvider
from tests.event_spy import EventSpy


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


@pytest.mark.asyncio
async def test_agent_runtime_switch_publishes_agent_changed_event():
    provider = MockLLMProvider()
    old_tools = EmptyToolLibrary()
    new_tools = EmptyToolLibrary()
    event_bus = SimpleEventBus()
    event_spy = EventSpy()
    event_bus.subscribe(AgentChangedEvent, event_spy.record_event)
    agent_id = AgentId("Agent")
    agent = Agent(
        agent_id=agent_id,
        agent_name="Old Agent",
        tools=old_tools,
        llm_provider=provider,
        model_name="default-model",
        user_input=Input(DummyUserInput()),
        event_bus=event_bus,
        context=Messages(system_prompt="old system prompt"),
    )

    new_brain = Brain(
        name="New Agent",
        system_prompt="new system prompt",
        tools=new_tools,
        model_name="new-model",
    )

    agent.update_brain(new_brain)

    actual = event_spy.get_events(AgentChangedEvent)
    assert len(actual) == 1
    assert actual[0].agent_id == agent_id
    assert actual[0].old_name == "Old Agent"
    assert actual[0].new_name == "New Agent"


@pytest.mark.asyncio
async def test_agent_runtime_switch_publishes_model_changed_before_agent_changed_event():
    provider = MockLLMProvider()
    event_bus = SimpleEventBus()
    event_spy = EventSpy()
    event_bus.subscribe(ModelChangedEvent, event_spy.record_event)
    event_bus.subscribe(AgentChangedEvent, event_spy.record_event)
    agent_id = AgentId("Agent")
    agent = Agent(
        agent_id=agent_id,
        agent_name="Old Agent",
        tools=EmptyToolLibrary(),
        llm_provider=provider,
        model_name="default-model",
        user_input=Input(DummyUserInput()),
        event_bus=event_bus,
        context=Messages(system_prompt="old system prompt"),
    )

    new_brain = Brain(
        name="New Agent",
        system_prompt="new system prompt",
        tools=EmptyToolLibrary(),
        model_name="new-model",
    )

    agent.update_brain(new_brain)

    ordered_relevant_events = [
        event
        for event in event_spy.get_all_events()
        if isinstance(event, (ModelChangedEvent, AgentChangedEvent))
    ]
    assert len(ordered_relevant_events) == 2
    assert isinstance(ordered_relevant_events[0], ModelChangedEvent)
    assert ordered_relevant_events[0].agent_id == agent_id
    assert ordered_relevant_events[0].old_model == "default-model"
    assert ordered_relevant_events[0].new_model == "new-model"
    assert isinstance(ordered_relevant_events[1], AgentChangedEvent)
    assert ordered_relevant_events[1].agent_id == agent_id
    assert ordered_relevant_events[1].old_name == "Old Agent"
    assert ordered_relevant_events[1].new_name == "New Agent"
