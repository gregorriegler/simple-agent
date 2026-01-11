import asyncio

import pytest
from approvaltests import verify

from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    ModelChangedEvent,
    SessionClearedEvent,
    ToolResultEvent,
    UserPromptedEvent,
)
from simple_agent.application.llm_stub import StubLLMProvider, create_llm_stub
from simple_agent.application.session import Session, SessionArgs
from simple_agent.infrastructure.event_logger import EventLogger
from simple_agent.infrastructure.file_event_store import FileEventStore
from simple_agent.infrastructure.subscribe_events import subscribe_events
from simple_agent.infrastructure.textual.textual_app import TextualApp
from tests.infrastructure.textual.test_utils import (
    MockUserInput,
    dump_ascii_screen,
    dump_ui_state,
)
from tests.session_test_bed import TestAgentLibrary, _NoOpTodoCleanup
from tests.test_helpers import DummyProjectTree
from tests.test_tool_library import ToolLibraryFactoryStub


@pytest.mark.asyncio
async def test_continuation_ui_golden_master(tmp_path):
    event_store = FileEventStore(tmp_path)
    agent_id = AgentId("Agent").with_root(tmp_path)

    # --- Part 1: Initial Session ---
    llm_responses = [
        "Starting subagent\n🛠️[subagent coding Say hello /]",
        "Subagent is talking...",
    ]

    def create_session_and_app(responses):
        bus = SimpleEventBus()
        user_input = MockUserInput()
        llm = create_llm_stub(responses)
        tool_factory = ToolLibraryFactoryStub(llm, event_bus=bus)

        session = Session(
            event_bus=bus,
            tool_library_factory=tool_factory,
            agent_library=TestAgentLibrary(),
            user_input=user_input,
            todo_cleanup=_NoOpTodoCleanup(),
            llm_provider=StubLLMProvider.for_testing(llm),
            project_tree=DummyProjectTree(),
            event_store=event_store,
        )

        app = TextualApp(user_input, agent_id, available_models=["stub-model"])

        # Subscribe event store to bus
        for et in [
            UserPromptedEvent,
            AssistantRespondedEvent,
            AgentStartedEvent,
            AgentFinishedEvent,
            ToolResultEvent,
            SessionClearedEvent,
            ModelChangedEvent,
        ]:
            bus.subscribe(et, event_store.persist)

        subscribe_events(bus, EventLogger(), _NoOpTodoCleanup(), app, event_store)

        return session, app

    session1, app1 = create_session_and_app(llm_responses)

    async with app1.run_test(size=(80, 24)) as pilot:
        asyncio.create_task(
            session1.run_async(SessionArgs(start_message="Start the process"), agent_id)
        )

        for _ in range(15):
            await pilot.pause(0.1)

        state_before = f"--- BEFORE CONTINUATION ---\n{dump_ascii_screen(app1)}\n{dump_ui_state(app1)}"

    # --- Part 2: Continuation ---
    llm_responses_cont = ["Continuing..."]
    session2, app2 = create_session_and_app(llm_responses_cont)

    async with app2.run_test(size=(80, 24)) as pilot:
        asyncio.create_task(
            session2.run_async(SessionArgs(continue_session=True), agent_id)
        )

        for _ in range(15):
            await pilot.pause(0.1)

        state_after = f"--- AFTER CONTINUATION ---\n{dump_ascii_screen(app2)}\n{dump_ui_state(app2)}"

        verify(state_before + "\n\n" + state_after)
