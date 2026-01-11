from typing import cast

import pytest
from approvaltests import verify
from textual.timer import Timer

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_type import AgentType
from simple_agent.application.events import (
    AgentStartedEvent,
    AssistantRespondedEvent,
    SessionStartedEvent,
    UserPromptedEvent,
)
from simple_agent.infrastructure.file_event_store import FileEventStore
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
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

    class DummyTimer:
        def stop(self) -> None:
            return None

    def noop_set_interval(*args: object, **kwargs: object) -> Timer:
        return cast(Timer, DummyTimer())

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
        user_input=None, root_agent_id=agent_id, available_models=["stub-model"]
    )
    app1.set_interval = noop_set_interval

    async with app1.run_test(size=(80, 24)) as pilot:
        # Replay events to build UI state
        for event in events:
            app1.on_domain_event_message(DomainEventMessage(event))
        await pilot.pause()

        state_before = f"--- UI STATE FROM DIRECT EVENT REPLAY ---\n{dump_ascii_screen(app1)}\n{dump_ui_state(app1)}"

    # --- Part 2: Build UI by loading from event store (continuation path) ---
    app2 = TextualApp(
        user_input=None, root_agent_id=agent_id, available_models=["stub-model"]
    )
    app2.set_interval = noop_set_interval

    async with app2.run_test(size=(80, 24)) as pilot:
        # Load all events from store in chronological order and replay
        for event in event_store.load_all_events():
            app2.on_domain_event_message(DomainEventMessage(event))

        await pilot.pause()

        state_after = f"--- UI STATE FROM EVENT STORE CONTINUATION ---\n{dump_ascii_screen(app2)}\n{dump_ui_state(app2)}"

    verify(state_before + "\n\n" + state_after)
