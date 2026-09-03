from simple_agent.application.llm import (
    AssistantMessage,
    LLMResponse,
    Messages,
    ToolResultMessage,
)
from simple_agent.application.tool_library import RawToolCall


def test_llm_response_defaults_usage():
    response = LLMResponse(answer="Hello")

    assert response.usage is not None
    assert response.usage.total_tokens == 0


def test_messages_replaces_seeded_system_prompt():
    messages = Messages([{"role": "system", "content": "old"}], system_prompt="new")

    assert messages.to_list()[0]["content"] == "new"


def test_messages_clear_keeps_system_prompt():
    messages = Messages(system_prompt="system")
    messages.user_says("hello")

    messages.clear()

    assert len(messages) == 1
    assert messages.to_list()[0]["role"] == "system"


def test_messages_ignores_empty_user_message():
    messages = Messages()

    messages.user_says("")

    assert len(messages) == 0


def test_messages_records_an_assistant_turn_with_its_tool_calls():
    messages = Messages()
    calls = [RawToolCall(name="bash", arguments="ls")]

    messages.assistant_turn("on it", calls)

    assert messages.to_list() == [AssistantMessage("on it", calls)]


def test_messages_records_an_assistant_tool_call_turn_with_empty_text():
    messages = Messages()
    calls = [RawToolCall(name="bash", arguments="ls")]

    messages.assistant_turn("", calls)

    assert messages.to_list() == [AssistantMessage("", calls)]


def test_messages_records_a_tool_result_turn():
    messages = Messages()
    call = RawToolCall(name="bash", arguments="ls")

    messages.tool_result(call, "a.txt\nb.txt")

    assert messages.to_list() == [ToolResultMessage(call, "a.txt\nb.txt")]
