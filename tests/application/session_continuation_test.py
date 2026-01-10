import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    UserPromptedEvent,
)
from simple_agent.infrastructure.file_event_store import FileEventStore
from tests.session_test_bed import CapturingLLM, SessionTestBed


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
            max_tokens=100,
            input_tokens=50,
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
            response="🛠️[subagent coding Do something /]",
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
            "🛠️[subagent coding Continue subagent work /]",
            "🛠️[complete-task Subagent done /]",
            "🛠️[complete-task Parent done /]",
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
