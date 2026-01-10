from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    SessionClearedEvent,
    ToolResultEvent,
    UserPromptedEvent,
)
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.file_event_store import FileEventStore


class TestFileEventStore:
    def test_persist_and_load_events(self, tmp_path):
        store = FileEventStore(tmp_path)
        event = UserPromptedEvent(agent_id=AgentId("Agent"), input_text="Hello")

        store.persist(event)
        events = store.load_all_events()

        assert len(events) == 1
        assert isinstance(events[0], UserPromptedEvent)
        assert events[0].input_text == "Hello"

    def test_load_events_filtered_by_agent(self, tmp_path):
        store = FileEventStore(tmp_path)
        store.persist(UserPromptedEvent(agent_id=AgentId("Agent"), input_text="First"))
        store.persist(
            UserPromptedEvent(agent_id=AgentId("Agent/Coding"), input_text="Second")
        )
        store.persist(UserPromptedEvent(agent_id=AgentId("Agent"), input_text="Third"))

        events = store.load_events(AgentId("Agent"))

        assert len(events) == 2
        assert isinstance(events[0], UserPromptedEvent)
        assert isinstance(events[1], UserPromptedEvent)
        assert events[0].input_text == "First"
        assert events[1].input_text == "Third"

    def test_load_all_events_preserves_order(self, tmp_path):
        store = FileEventStore(tmp_path)
        store.persist(UserPromptedEvent(agent_id=AgentId("Agent"), input_text="1"))
        store.persist(UserPromptedEvent(agent_id=AgentId("Agent"), input_text="2"))
        store.persist(UserPromptedEvent(agent_id=AgentId("Agent"), input_text="3"))

        events = store.load_all_events()

        assert len(events) == 3
        assert all(isinstance(e, UserPromptedEvent) for e in events)
        input_texts = [e.input_text for e in events if isinstance(e, UserPromptedEvent)]
        assert input_texts == ["1", "2", "3"]

    def test_empty_store_returns_empty_list(self, tmp_path):
        store = FileEventStore(tmp_path)

        events = store.load_all_events()

        assert events == []

    def test_persist_multiple_event_types(self, tmp_path):
        store = FileEventStore(tmp_path)
        agent_id = AgentId("Agent")

        store.persist(UserPromptedEvent(agent_id=agent_id, input_text="Hello"))
        store.persist(
            AssistantRespondedEvent(
                agent_id=agent_id,
                response="Hi!",
                model="test-model",
                max_tokens=100,
                input_tokens=50,
            )
        )
        store.persist(
            AgentStartedEvent(
                agent_id=AgentId("Agent/Sub"), agent_name="Sub", model="m"
            )
        )
        store.persist(AgentFinishedEvent(agent_id=AgentId("Agent/Sub")))
        store.persist(
            ToolResultEvent(
                agent_id=agent_id,
                call_id="call-1",
                result=SingleToolResult(message="result"),
            )
        )
        store.persist(SessionClearedEvent(agent_id=agent_id))

        events = store.load_all_events()

        assert len(events) == 6
        assert isinstance(events[0], UserPromptedEvent)
        assert isinstance(events[1], AssistantRespondedEvent)
        assert isinstance(events[2], AgentStartedEvent)
        assert isinstance(events[3], AgentFinishedEvent)
        assert isinstance(events[4], ToolResultEvent)
        assert isinstance(events[5], SessionClearedEvent)

    def test_handles_corrupted_lines_gracefully(self, tmp_path):
        store = FileEventStore(tmp_path)
        store.persist(UserPromptedEvent(agent_id=AgentId("Agent"), input_text="Good"))

        events_file = tmp_path / "events.jsonl"
        with open(events_file, "a", encoding="utf-8") as f:
            f.write("not valid json\n")

        store.persist(
            UserPromptedEvent(agent_id=AgentId("Agent"), input_text="Also good")
        )

        events = store.load_all_events()

        assert len(events) == 2
        assert isinstance(events[0], UserPromptedEvent)
        assert isinstance(events[1], UserPromptedEvent)
        assert events[0].input_text == "Good"
        assert events[1].input_text == "Also good"

    def test_load_events_with_none_agent_id_filter(self, tmp_path):
        store = FileEventStore(tmp_path)
        store.persist(UserPromptedEvent(agent_id=AgentId("Agent"), input_text="First"))
        store.persist(UserPromptedEvent(agent_id=AgentId("Other"), input_text="Second"))

        events = store.load_events(None)

        assert len(events) == 2
