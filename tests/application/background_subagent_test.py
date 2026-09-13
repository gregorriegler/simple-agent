import asyncio

import pytest

from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_task_manager import AgentTaskManager
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.event_store import NoOpEventStore
from simple_agent.application.events import (
    AgentFinishedEvent,
    ToolResultEvent,
    UserPromptedEvent,
    UserPromptRequestedEvent,
)
from simple_agent.application.llm_stub import create_llm_stub
from simple_agent.application.routed_user_input import RoutedUserInput
from simple_agent.infrastructure.file_intents import FileIntents
from simple_agent.tools.all_tools import AllToolsFactory
from tests.session_test_bed import AgentLibraryStub, SessionTestBed
from tests.test_helpers import DummyProjectTree
from tests.test_tool_library import FixedLLMProvider
from tests.tool_calls import bash, complete_task, subagent, wait
from tests.user_input_stub import UserInputStub

pytestmark = pytest.mark.asyncio


async def test_background_subagent_finishes_on_complete_task_without_asking_for_input():
    subagent_id = AgentId("Agent/Coding")
    llm = create_llm_stub(
        [
            subagent("coding", "do the sub task", background=True),
            "parent carries on",
            complete_task("sub done"),
        ]
    )

    result = await SessionTestBed().with_llm(llm).run()

    result.assert_event_occured(AgentFinishedEvent(subagent_id))
    asked = [
        e
        for e in result.events.get_all_events()
        if isinstance(e, UserPromptRequestedEvent) and e.agent_id == subagent_id
    ]
    assert asked == []


async def test_background_subagent_reports_its_summary_to_the_parent_input():
    factory = _factory(FixedLLMProvider(create_llm_stub([complete_task("sub done")])))
    parent_input = factory.create_input(AgentId("Agent"))
    spawn = factory.create_spawner(AgentId("Agent"), parent_input)

    await spawn(AgentType("coding"), "do the sub task", True)
    await asyncio.gather(*_other_tasks())

    assert parent_input.drain() == ["Subagent Agent/Coding completed: sub done"]


async def test_background_subagent_that_fails_reports_the_failure():
    factory = _factory(FixedLLMProvider(FailingLLM("boom")))
    parent_input = factory.create_input(AgentId("Agent"))
    spawn = factory.create_spawner(AgentId("Agent"), parent_input)

    await spawn(AgentType("coding"), "do the sub task", True)
    await asyncio.gather(*_other_tasks())

    assert parent_input.drain() == ["Subagent Agent/Coding failed: boom"]


class FailingLLM:
    def __init__(self, error: str):
        self._error = error

    @property
    def model(self) -> str:
        return "failing-model"

    async def call_async(self, messages):
        raise RuntimeError(self._error)


async def test_parent_receives_the_background_subagent_summary_as_a_prompt():
    llm = create_llm_stub(
        [
            subagent("coding", "do the sub task", background=True),
            bash("sleep 0.3"),
            complete_task("sub done"),
            "parent carries on",
        ]
    )

    result = await SessionTestBed().with_llm(llm).run()

    result.assert_event_occured(
        UserPromptedEvent(AgentId("Agent"), "Subagent Agent/Coding completed: sub done")
    )


async def test_parent_receives_a_background_command_output_as_a_prompt():
    llm = create_llm_stub(
        [
            bash("sleep 0.1; echo done", background=True),
            bash("sleep 0.5"),
            "parent carries on",
        ]
    )

    result = await SessionTestBed().with_llm(llm).run()

    prompts = [
        e.input_text
        for e in result.events.get_all_events()
        if isinstance(e, UserPromptedEvent) and e.agent_id == AgentId("Agent")
    ]
    assert len(prompts) == 2
    assert prompts[1].startswith(
        "Background command `sleep 0.1; echo done` finished:\n✅ Exit code 0 ("
    )
    assert prompts[1].endswith("\n\ndone")


async def test_parent_waits_for_a_background_command():
    llm = create_llm_stub(
        [
            bash("sleep 0.2; echo done", background=True),
            wait(timeout=5),
            "parent carries on",
        ]
    )

    result = await SessionTestBed().with_llm(llm).run()

    tool_results = [
        e.result.message
        for e in result.events.get_all_events()
        if isinstance(e, ToolResultEvent)
    ]
    assert tool_results[1] == "A message arrived."
    prompts = [
        e.input_text
        for e in result.events.get_all_events()
        if isinstance(e, UserPromptedEvent) and e.agent_id == AgentId("Agent")
    ]
    assert prompts[1].startswith("Background command `sleep 0.2; echo done` finished:")


async def test_background_subagent_that_ends_with_text_does_not_take_the_parents_message():
    keyboard = RoutedUserInput()
    event_bus = SimpleEventBus()
    factory = _factory(
        FixedLLMProvider(create_llm_stub(["done, I think"])), keyboard, event_bus
    )
    parent_input = factory.create_input(AgentId("Agent"))
    spawn = factory.create_spawner(AgentId("Agent"), parent_input)
    subagent_waits = asyncio.Event()
    event_bus.subscribe(UserPromptRequestedEvent, lambda _: subagent_waits.set())

    await spawn(AgentType("coding"), "do the sub task", True)
    await asyncio.wait_for(subagent_waits.wait(), timeout=2)
    keyboard.submit_input(AgentId("Agent"), "for the parent")

    assert await asyncio.wait_for(parent_input.read_async(), timeout=2) == (
        "for the parent"
    )
    keyboard.close()
    await asyncio.gather(*_other_tasks(), return_exceptions=True)


def _factory(llm_provider, user_input=None, event_bus=None) -> AgentFactory:
    return AgentFactory(
        event_bus=event_bus or SimpleEventBus(),
        tool_library_factory=AllToolsFactory(FileIntents()),
        agent_library=AgentLibraryStub(),
        user_input=user_input or UserInputStub(),
        llm_provider=llm_provider,
        project_tree=DummyProjectTree(),
        event_store=NoOpEventStore(),
        agent_task_manager=AgentTaskManager(),
    )


def _other_tasks():
    return [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
