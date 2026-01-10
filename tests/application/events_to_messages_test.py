from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    SessionClearedEvent,
    ToolResultEvent,
    UserPromptedEvent,
)
from simple_agent.application.events_to_messages import events_to_messages
from simple_agent.application.tool_results import SingleToolResult


class TestEventsToMessages:
    def test_converts_user_prompted_to_user_message(self):
        agent_id = AgentId("Agent")
        events = [UserPromptedEvent(agent_id=agent_id, input_text="Hello")]

        messages = events_to_messages(events, agent_id)

        message_list = messages.to_list()
        assert len(message_list) == 1
        assert message_list[0]["role"] == "user"
        assert message_list[0]["content"] == "Hello"

    def test_converts_assistant_responded_to_assistant_message(self):
        agent_id = AgentId("Agent")
        events = [
            AssistantRespondedEvent(
                agent_id=agent_id,
                response="Hi there!",
                model="test-model",
                max_tokens=100,
                input_tokens=50,
            )
        ]

        messages = events_to_messages(events, agent_id)

        message_list = messages.to_list()
        assert len(message_list) == 1
        assert message_list[0]["role"] == "assistant"
        assert message_list[0]["content"] == "Hi there!"

    def test_converts_tool_result_to_user_message(self):
        agent_id = AgentId("Agent")
        events = [
            ToolResultEvent(
                agent_id=agent_id,
                call_id="call-1",
                result=SingleToolResult(message="Tool output here"),
            )
        ]

        messages = events_to_messages(events, agent_id)

        message_list = messages.to_list()
        assert len(message_list) == 1
        assert message_list[0]["role"] == "user"
        assert message_list[0]["content"] == "Tool output here"

    def test_session_cleared_resets_messages(self):
        agent_id = AgentId("Agent")
        events = [
            UserPromptedEvent(agent_id=agent_id, input_text="First"),
            AssistantRespondedEvent(agent_id=agent_id, response="Response"),
            SessionClearedEvent(agent_id=agent_id),
            UserPromptedEvent(agent_id=agent_id, input_text="After clear"),
        ]

        messages = events_to_messages(events, agent_id)

        message_list = messages.to_list()
        assert len(message_list) == 1
        assert message_list[0]["content"] == "After clear"

    def test_filters_by_agent_id(self):
        agent_id = AgentId("Agent")
        other_id = AgentId("Other")
        events = [
            UserPromptedEvent(agent_id=agent_id, input_text="For Agent"),
            UserPromptedEvent(agent_id=other_id, input_text="For Other"),
            AssistantRespondedEvent(agent_id=agent_id, response="Agent response"),
        ]

        messages = events_to_messages(events, agent_id)

        message_list = messages.to_list()
        assert len(message_list) == 2
        assert message_list[0]["content"] == "For Agent"
        assert message_list[1]["content"] == "Agent response"

    def test_ignores_agent_started_and_finished_events(self):
        agent_id = AgentId("Agent")
        events = [
            AgentStartedEvent(agent_id=agent_id, agent_name="Agent", model="model"),
            UserPromptedEvent(agent_id=agent_id, input_text="Hello"),
            AgentFinishedEvent(agent_id=agent_id),
        ]

        messages = events_to_messages(events, agent_id)

        message_list = messages.to_list()
        assert len(message_list) == 1
        assert message_list[0]["content"] == "Hello"

    def test_full_conversation_flow(self):
        agent_id = AgentId("Agent")
        events = [
            UserPromptedEvent(agent_id=agent_id, input_text="Do something"),
            AssistantRespondedEvent(
                agent_id=agent_id, response="I'll use a tool 🛠️[bash ls /]"
            ),
            ToolResultEvent(
                agent_id=agent_id,
                call_id="call-1",
                result=SingleToolResult(message="file1.txt\nfile2.txt"),
            ),
            AssistantRespondedEvent(agent_id=agent_id, response="Found 2 files"),
        ]

        messages = events_to_messages(events, agent_id)

        message_list = messages.to_list()
        assert len(message_list) == 4
        assert message_list[0] == {"role": "user", "content": "Do something"}
        assert message_list[1] == {
            "role": "assistant",
            "content": "I'll use a tool 🛠️[bash ls /]",
        }
        assert message_list[2] == {"role": "user", "content": "file1.txt\nfile2.txt"}
        assert message_list[3] == {"role": "assistant", "content": "Found 2 files"}

    def test_empty_events_returns_empty_messages(self):
        agent_id = AgentId("Agent")

        messages = events_to_messages([], agent_id)

        assert len(messages.to_list()) == 0

    def test_tool_result_with_none_result_is_skipped(self):
        agent_id = AgentId("Agent")
        events = [
            ToolResultEvent(agent_id=agent_id, call_id="call-1", result=None),
        ]

        messages = events_to_messages(events, agent_id)

        assert len(messages.to_list()) == 0
