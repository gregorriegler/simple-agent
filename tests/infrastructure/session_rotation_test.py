from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import SessionClearedEvent, UserPromptedEvent
from simple_agent.infrastructure.file_event_store import FileEventStore
from simple_agent.infrastructure.file_session_storage import FileSessionStorage
from simple_agent.infrastructure.subscribe_events import subscribe_persistence

AGENT = AgentId("Agent")


def _storage(tmp_path):
    return FileSessionStorage.create(
        tmp_path / "sessions", continue_session=False, cwd=tmp_path
    )


def test_clearing_starts_a_new_session(tmp_path):
    storage = _storage(tmp_path)
    event_bus = SimpleEventBus()
    subscribe_persistence(event_bus, FileEventStore(storage), storage)
    cleared_session = storage.session_root()

    event_bus.publish(UserPromptedEvent(agent_id=AGENT, input_text="Before"))
    event_bus.publish(SessionClearedEvent(agent_id=AGENT))
    event_bus.publish(UserPromptedEvent(agent_id=AGENT, input_text="After"))

    assert storage.session_root() != cleared_session
    cleared_log = (cleared_session / "events.jsonl").read_text(encoding="utf-8")
    assert "Before" in cleared_log
    assert "SessionClearedEvent" in cleared_log
    assert "After" not in cleared_log


def test_continuing_after_a_clear_only_sees_the_new_session(tmp_path):
    storage = _storage(tmp_path)
    event_bus = SimpleEventBus()
    subscribe_persistence(event_bus, FileEventStore(storage), storage)

    event_bus.publish(UserPromptedEvent(agent_id=AGENT, input_text="Before"))
    event_bus.publish(SessionClearedEvent(agent_id=AGENT))
    event_bus.publish(UserPromptedEvent(agent_id=AGENT, input_text="After"))

    continued = FileSessionStorage.create(
        tmp_path / "sessions", continue_session=True, cwd=tmp_path
    )
    events = FileEventStore(continued).load_all_events()

    assert [e.input_text for e in events] == ["After"]
