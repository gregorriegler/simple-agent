import pytest
from approvaltests import verify

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_task_manager import AgentTaskManager
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptedEvent,
)
from simple_agent.application.history_replayer import HistoryReplayer
from simple_agent.application.tool_library import ParsedTool, RawToolCall
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.file_event_store import FileEventStore
from simple_agent.infrastructure.subscribe_events import subscribe_events
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from tests.infrastructure.textual.conftest import FakeEventLogger, FakeTodoCleanup
from tests.infrastructure.textual.test_utils import (
    dump_ascii_screen,
    dump_ui_state,
)


@pytest.mark.asyncio
async def test_continuation_ui_shows_same_content_after_restore(tmp_path):
    """
    Test that UI looks the same after session continuation.

    This test:
    1. Creates an event store with saved events (simulating a previous session)
    2. Starts a new app and replays events to build UI state ("BEFORE")
    3. Creates another app and uses continuation to restore from event store ("AFTER")
    4. Verifies both UIs show the same content
    """

    event_store = FileEventStore(tmp_path)
    agent_id = AgentId("Agent").with_root(tmp_path)
    subagent_id = AgentId("Agent/Coding").with_root(tmp_path)

    # Persist events to the event store (simulating a previous session)
    events = [
        SessionStartedEvent(agent_id=agent_id, is_continuation=False),
        AgentStartedEvent(
            agent_id=agent_id,
            agent_name="Agent",
            model="stub-model",
            agent_type=AgentType("agent"),
        ),
        UserPromptedEvent(agent_id=agent_id, input_text="Start the process"),
        AssistantRespondedEvent(
            agent_id=agent_id,
            response="Thinking...",
            model="stub-model",
            token_usage_display="0.0%",
        ),
        ToolCalledEvent(
            agent_id=agent_id,
            call_id="call-1",
            tool=ParsedTool(RawToolCall("read_file", "test.txt"), None),
        ),
        ToolResultEvent(
            agent_id=agent_id,
            call_id="call-1",
            result=SingleToolResult(
                "Content of test.txt", display_title="Reading test.txt"
            ),
        ),
        AssistantRespondedEvent(
            agent_id=agent_id,
            response="Starting subagent\n🛠️[subagent coding Say hello /]",
            model="stub-model",
            token_usage_display="0.0%",
        ),
        AgentStartedEvent(
            agent_id=subagent_id,
            agent_name="Coding",
            model="stub-model",
            agent_type=AgentType("coding"),
        ),
        UserPromptedEvent(agent_id=subagent_id, input_text="Say hello"),
        AssistantRespondedEvent(
            agent_id=subagent_id,
            response="Hello from subagent!",
            model="stub-model",
            token_usage_display="0.0%",
        ),
    ]

    for event in events:
        event_store.persist(event)

    # --- Part 1: Build UI by replaying events directly ---
    app1 = TextualApp(
        user_input=None,
        root_agent_id=agent_id,
        agent_task_manager=AgentTaskManager(),
        available_models=["stub-model"],
    )

    async with app1.run_test(size=(80, 24)) as pilot:
        for event in events:
            app1.on_domain_event_message(DomainEventMessage(event))
        await pilot.pause()

        state_before = f"--- UI STATE FROM DIRECT EVENT REPLAY ---\n{dump_ascii_screen(app1)}\n{dump_ui_state(app1)}"

    # --- Part 2: Build UI using the real HistoryReplayer (continuation path) ---
    event_bus = SimpleEventBus()
    app2 = TextualApp(
        user_input=None,
        root_agent_id=agent_id,
        agent_task_manager=AgentTaskManager(),
        available_models=["stub-model"],
    )
    subscribe_events(event_bus, FakeEventLogger(), FakeTodoCleanup(), app2)

    async with app2.run_test(size=(80, 24)) as pilot:
        replayer = HistoryReplayer(event_bus, event_store)
        await replayer.replay_all_agents_async(agent_id)
        await pilot.pause()

        state_after = f"--- UI STATE FROM EVENT STORE CONTINUATION ---\n{dump_ascii_screen(app2)}\n{dump_ui_state(app2)}"

    verify(state_before + "\n\n" + state_after)


@pytest.mark.asyncio
async def test_continuation_tool_result_is_last_event(tmp_path):
    """
    When the last persisted event is a ToolResultEvent, continuation should
    show the completed tool result, not a loading spinner.

    Reproduces the real-world scenario: user runs a tool, it completes,
    then they close and continue the session.
    """
    event_store = FileEventStore(tmp_path)
    agent_id = AgentId("Agent").with_root(tmp_path)

    # This matches the real event sequence from a session where a tool
    # was called and completed before the session was closed.
    events = [
        AgentStartedEvent(
            agent_id=agent_id,
            agent_name="Agent",
            model="stub-model",
            agent_type=AgentType("agent"),
        ),
        UserPromptedEvent(agent_id=agent_id, input_text="run bash sleep 5"),
        AssistantRespondedEvent(
            agent_id=agent_id,
            response="🛠️[bash sleep 5 /]",
            model="stub-model",
            token_usage_display="0.4%",
        ),
        ToolCalledEvent(
            agent_id=agent_id,
            call_id="Agent::tool_call::1",
            tool=ParsedTool(RawToolCall("bash", "sleep 5"), None),
        ),
        ToolResultEvent(
            agent_id=agent_id,
            call_id="Agent::tool_call::1",
            result=SingleToolResult("Exit code 0 (5.017s elapsed)"),
        ),
        AssistantRespondedEvent(
            agent_id=agent_id,
            response="Done.",
            model="stub-model",
            token_usage_display="0.4%",
        ),
        AssistantSaidEvent(agent_id=agent_id, message="Done."),
        AgentFinishedEvent(agent_id=agent_id),
    ]

    for event in events:
        event_store.persist(event)

    # --- Part 1: Build UI by replaying events directly ---
    app1 = TextualApp(
        user_input=None,
        root_agent_id=agent_id,
        agent_task_manager=AgentTaskManager(),
        available_models=["stub-model"],
    )

    async with app1.run_test(size=(80, 24)) as pilot:
        for event in events:
            app1.on_domain_event_message(DomainEventMessage(event))
        await pilot.pause()

        state_before = f"--- UI STATE FROM DIRECT EVENT REPLAY ---\n{dump_ascii_screen(app1)}\n{dump_ui_state(app1)}"

    # --- Part 2: Build UI using the real HistoryReplayer ---
    event_bus = SimpleEventBus()
    app2 = TextualApp(
        user_input=None,
        root_agent_id=agent_id,
        agent_task_manager=AgentTaskManager(),
        available_models=["stub-model"],
    )
    subscribe_events(event_bus, FakeEventLogger(), FakeTodoCleanup(), app2)

    async with app2.run_test(size=(80, 24)) as pilot:
        replayer = HistoryReplayer(event_bus, event_store)
        await replayer.replay_all_agents_async(agent_id)
        await pilot.pause()

        state_after = f"--- UI STATE FROM EVENT STORE CONTINUATION ---\n{dump_ascii_screen(app2)}\n{dump_ui_state(app2)}"

    verify(state_before + "\n\n" + state_after)
