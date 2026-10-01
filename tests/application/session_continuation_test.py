import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    SessionInterruptedEvent,
    ToolCalledEvent,
    UserPromptedEvent,
    UserPromptRequestedEvent,
)
from simple_agent.infrastructure.file_event_store import FileEventStore
from tests.session_test_bed import CapturingLLM, SessionTestBed
from tests.tool_calls import cat, complete_task, subagent


@pytest.mark.asyncio
async def test_continued_session_loads_previous_messages_into_llm(tmp_path):
    agent_id = AgentId("Agent")
    event_store = FileEventStore(tmp_path)
    event_store.persist(UserPromptedEvent(agent_id=agent_id, input_text="Hello"))
    event_store.persist(
        AssistantRespondedEvent(
            agent_id=agent_id,
            response="Hi there!",
            model="test-model",
            token_usage_display="50.0%",
        )
    )

    capturing_llm = CapturingLLM()

    await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm(capturing_llm)
        .continuing_session()
        .with_user_inputs("Continue please")
        .run()
    )

    assert capturing_llm.first_call_contained("user", "Hello")
    assert capturing_llm.first_call_contained("assistant", "Hi there!")


@pytest.mark.asyncio
async def test_continued_session_restores_subagent_messages(tmp_path):
    parent_id = AgentId("Agent")
    subagent_id = AgentId("Agent/Coding")

    event_store = FileEventStore(tmp_path)
    event_store.persist(UserPromptedEvent(agent_id=parent_id, input_text="Parent task"))
    event_store.persist(
        AssistantRespondedEvent(
            agent_id=parent_id,
            response="Starting subagent",
        )
    )
    event_store.persist(
        AgentStartedEvent(agent_id=subagent_id, agent_name="Coding", model="test-model")
    )
    event_store.persist(
        UserPromptedEvent(agent_id=subagent_id, input_text="Do something")
    )
    event_store.persist(
        AssistantRespondedEvent(
            agent_id=subagent_id,
            response="Subagent previous work",
        )
    )
    event_store.persist(AgentFinishedEvent(agent_id=subagent_id))

    capturing_llm = CapturingLLM()
    capturing_llm.set_responses(
        [
            subagent("coding", "Continue subagent work"),
            complete_task("Subagent done"),
            complete_task("Parent done"),
        ]
    )

    await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm(capturing_llm)
        .continuing_session()
        .with_user_inputs("Continue")
        .run()
    )

    assert capturing_llm.call_contained(1, "user", "Do something")
    assert capturing_llm.call_contained(1, "assistant", "Subagent previous work")


@pytest.mark.asyncio
async def test_a_subagent_running_when_the_user_quits_is_resumed(tmp_path):
    event_store = FileEventStore(tmp_path)
    await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm_responses([subagent("coding", "read hello"), cat("hello.txt")])
        .with_user_inputs("Create a subagent that reads hello")
        .quitting_when(ToolCalledEvent, on_tab="Agent/Coding")
        .run()
    )

    asking = []
    await (
        SessionTestBed()
        .with_event_store(event_store)
        .continuing_session()
        .on_event(UserPromptRequestedEvent, lambda e: asking.append(e.agent_id))
        .run()
    )

    assert AgentId("Agent/Coding") in asking


@pytest.mark.asyncio
async def test_escape_interrupts_a_resumed_subagent(tmp_path):
    event_store = FileEventStore(tmp_path)
    await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm_responses([subagent("coding", "read hello"), cat("hello.txt")])
        .with_user_inputs("Create a subagent that reads hello")
        .quitting_when(ToolCalledEvent, on_tab="Agent/Coding")
        .run()
    )

    interrupted = []
    await (
        SessionTestBed()
        .with_event_store(event_store)
        .continuing_session()
        .with_llm_responses(["Root is done", cat("hello.txt")])
        .typing_to("Agent/Coding", "Read it again", "")
        .cancelling_when(ToolCalledEvent, on_tab="Agent/Coding")
        .on_event(SessionInterruptedEvent, lambda e: interrupted.append(e.agent_id))
        .run()
    )

    assert interrupted == [AgentId("Agent/Coding")]
