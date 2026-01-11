import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_serializer import EventSerializer
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    ModelChangedEvent,
    SessionClearedEvent,
    ToolResultEvent,
    UserPromptedEvent,
)
from simple_agent.application.tool_results import SingleToolResult


class TestEventSerializer:
    def test_serialize_user_prompted_event(self):
        event = UserPromptedEvent(
            agent_id=AgentId("Agent"),
            input_text="Hello world",
        )

        result = EventSerializer.to_dict(event)

        assert result == {
            "type": "UserPromptedEvent",
            "agent_id": "Agent",
            "input_text": "Hello world",
        }

    def test_deserialize_user_prompted_event(self):
        data = {
            "type": "UserPromptedEvent",
            "agent_id": "Agent",
            "input_text": "Hello world",
        }

        result = EventSerializer.from_dict(data)

        assert isinstance(result, UserPromptedEvent)
        assert result.agent_id == AgentId("Agent")
        assert result.input_text == "Hello world"

    def test_serialize_assistant_responded_event(self):
        event = AssistantRespondedEvent(
            agent_id=AgentId("Agent"),
            response="Hi there!",
            model="claude-sonnet-4-20250514",
            token_usage_display="0.1%",
        )

        result = EventSerializer.to_dict(event)

        assert result == {
            "type": "AssistantRespondedEvent",
            "agent_id": "Agent",
            "response": "Hi there!",
            "model": "claude-sonnet-4-20250514",
            "token_usage_display": "0.1%",
        }

    def test_deserialize_assistant_responded_event(self):
        data = {
            "type": "AssistantRespondedEvent",
            "agent_id": "Agent",
            "response": "Hi there!",
            "model": "claude-sonnet-4-20250514",
            "token_usage_display": "0.1%",
        }

        result = EventSerializer.from_dict(data)

        assert isinstance(result, AssistantRespondedEvent)
        assert result.agent_id == AgentId("Agent")
        assert result.response == "Hi there!"
        assert result.model == "claude-sonnet-4-20250514"
        assert result.token_usage_display == "0.1%"

    def test_serialize_agent_started_event(self):
        event = AgentStartedEvent(
            agent_id=AgentId("Agent/Coding"),
            agent_name="Coding",
            model="claude-sonnet-4-20250514",
            agent_type="coding",
        )

        result = EventSerializer.to_dict(event)

        assert result == {
            "type": "AgentStartedEvent",
            "agent_id": "Agent/Coding",
            "agent_name": "Coding",
            "model": "claude-sonnet-4-20250514",
            "agent_type": "coding",
        }

    def test_deserialize_agent_started_event(self):
        data = {
            "type": "AgentStartedEvent",
            "agent_id": "Agent/Coding",
            "agent_name": "Coding",
            "model": "claude-sonnet-4-20250514",
            "agent_type": "coding",
        }

        result = EventSerializer.from_dict(data)

        assert isinstance(result, AgentStartedEvent)
        assert result.agent_id == AgentId("Agent/Coding")
        assert result.agent_name == "Coding"
        assert result.model == "claude-sonnet-4-20250514"

    def test_serialize_agent_finished_event(self):
        event = AgentFinishedEvent(agent_id=AgentId("Agent/Coding"))

        result = EventSerializer.to_dict(event)

        assert result == {
            "type": "AgentFinishedEvent",
            "agent_id": "Agent/Coding",
        }

    def test_deserialize_agent_finished_event(self):
        data = {
            "type": "AgentFinishedEvent",
            "agent_id": "Agent/Coding",
        }

        result = EventSerializer.from_dict(data)

        assert isinstance(result, AgentFinishedEvent)
        assert result.agent_id == AgentId("Agent/Coding")

    def test_serialize_tool_result_event(self):
        event = ToolResultEvent(
            agent_id=AgentId("Agent"),
            call_id="call-123",
            result=SingleToolResult(message="Tool output here"),
        )

        result = EventSerializer.to_dict(event)

        assert result == {
            "type": "ToolResultEvent",
            "agent_id": "Agent",
            "call_id": "call-123",
            "result_message": "Tool output here",
        }

    def test_deserialize_tool_result_event(self):
        data = {
            "type": "ToolResultEvent",
            "agent_id": "Agent",
            "call_id": "call-123",
            "result_message": "Tool output here",
        }

        result = EventSerializer.from_dict(data)

        assert isinstance(result, ToolResultEvent)
        assert result.agent_id == AgentId("Agent")
        assert result.call_id == "call-123"
        assert result.result is not None
        assert result.result.message == "Tool output here"

    def test_serialize_session_cleared_event(self):
        event = SessionClearedEvent(agent_id=AgentId("Agent"))

        result = EventSerializer.to_dict(event)

        assert result == {
            "type": "SessionClearedEvent",
            "agent_id": "Agent",
        }

    def test_deserialize_session_cleared_event(self):
        data = {
            "type": "SessionClearedEvent",
            "agent_id": "Agent",
        }

        result = EventSerializer.from_dict(data)

        assert isinstance(result, SessionClearedEvent)
        assert result.agent_id == AgentId("Agent")

    def test_serialize_model_changed_event(self):
        event = ModelChangedEvent(
            agent_id=AgentId("Agent"),
            old_model="claude-3-opus",
            new_model="claude-sonnet-4-20250514",
        )

        result = EventSerializer.to_dict(event)

        assert result == {
            "type": "ModelChangedEvent",
            "agent_id": "Agent",
            "old_model": "claude-3-opus",
            "new_model": "claude-sonnet-4-20250514",
        }

    def test_deserialize_model_changed_event(self):
        data = {
            "type": "ModelChangedEvent",
            "agent_id": "Agent",
            "old_model": "claude-3-opus",
            "new_model": "claude-sonnet-4-20250514",
        }

        result = EventSerializer.from_dict(data)

        assert isinstance(result, ModelChangedEvent)
        assert result.agent_id == AgentId("Agent")
        assert result.old_model == "claude-3-opus"
        assert result.new_model == "claude-sonnet-4-20250514"

    def test_round_trip_preserves_data(self):
        events = [
            UserPromptedEvent(agent_id=AgentId("Agent"), input_text="Test"),
            AssistantRespondedEvent(
                agent_id=AgentId("Agent"),
                response="Response",
                model="model",
                token_usage_display="50.0%",
            ),
            AgentStartedEvent(
                agent_id=AgentId("Agent/Sub"), agent_name="Sub", model="model"
            ),
            AgentFinishedEvent(agent_id=AgentId("Agent/Sub")),
            ToolResultEvent(
                agent_id=AgentId("Agent"),
                call_id="call-1",
                result=SingleToolResult(message="result"),
            ),
            SessionClearedEvent(agent_id=AgentId("Agent")),
            ModelChangedEvent(
                agent_id=AgentId("Agent"), old_model="old", new_model="new"
            ),
        ]

        for event in events:
            serialized = EventSerializer.to_dict(event)
            deserialized = EventSerializer.from_dict(serialized)
            re_serialized = EventSerializer.to_dict(deserialized)
            assert serialized == re_serialized

    def test_deserialize_with_null_agent_id(self):
        data = {
            "type": "UserPromptedEvent",
            "agent_id": None,
            "input_text": "Hello",
        }

        result = EventSerializer.from_dict(data)

        assert result.agent_id is None

    def test_deserialize_unknown_event_type_raises(self):
        data = {
            "type": "UnknownEvent",
            "agent_id": "Agent",
        }

        with pytest.raises(ValueError, match="Unknown event type"):
            EventSerializer.from_dict(data)
