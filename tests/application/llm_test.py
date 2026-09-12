from simple_agent.application.llm import (
    AssistantMessage,
    LLMResponse,
    Messages,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
    split_system_prompt,
)
from simple_agent.application.tool_library import ToolCall


def test_llm_response_defaults_usage():
    response = LLMResponse(answer="Hello")

    assert response.usage is not None
    assert response.usage.total_tokens == 0


def test_messages_replaces_seeded_system_prompt():
    messages = Messages([SystemMessage("old")], system_prompt="new")

    assert messages.to_list() == [SystemMessage("new")]


def test_messages_clear_keeps_system_prompt():
    messages = Messages(system_prompt="system")
    messages.user_says("hello")

    messages.clear()

    assert messages.to_list() == [SystemMessage("system")]


def test_messages_records_user_text_as_a_user_message():
    messages = Messages()

    messages.user_says("hello")

    assert messages.to_list() == [UserMessage("hello")]


def test_messages_ignores_empty_user_message():
    messages = Messages()

    messages.user_says("")

    assert len(messages) == 0


def test_messages_records_an_assistant_turn_with_its_tool_calls():
    messages = Messages()
    calls = [ToolCall("bash", {"command": "ls"})]

    messages.assistant_says("on it", calls)

    assert messages.to_list() == [AssistantMessage("on it", calls)]


def test_messages_records_an_assistant_tool_call_turn_with_empty_text():
    messages = Messages()
    calls = [ToolCall("bash", {"command": "ls"})]

    messages.assistant_says("", calls)

    assert messages.to_list() == [AssistantMessage("", calls)]


def test_messages_records_a_tool_result_turn():
    messages = Messages()
    call = ToolCall("bash", {"command": "ls"})

    messages.tool_result(call, "a.txt\nb.txt")

    assert messages.to_list() == [ToolResultMessage(call, "a.txt\nb.txt")]


class NamingRenderer:
    def system(self, message: SystemMessage) -> str:
        return f"system:{message.content}"

    def user(self, message: UserMessage) -> str:
        return f"user:{message.content}"

    def assistant(self, message: AssistantMessage) -> str:
        return f"assistant:{message.content}"

    def tool_result(self, message: ToolResultMessage) -> str:
        return f"tool_result:{message.content}"


def test_each_message_renders_through_its_own_renderer_method():
    call = ToolCall("bash", {"command": "ls"})
    messages = [
        SystemMessage("rules"),
        UserMessage("hi"),
        AssistantMessage("on it", [call]),
        ToolResultMessage(call, "a.txt"),
    ]

    rendered = [message.render(NamingRenderer()) for message in messages]

    assert rendered == [
        "system:rules",
        "user:hi",
        "assistant:on it",
        "tool_result:a.txt",
    ]


def test_messages_records_plain_assistant_text_as_an_assistant_message():
    messages = Messages()

    messages.assistant_says("hello")

    assert messages.to_list() == [AssistantMessage("hello")]


def test_splits_a_leading_system_prompt_off_the_history():
    messages = [SystemMessage("sys"), UserMessage("hi")]

    assert split_system_prompt(messages) == ("sys", [UserMessage("hi")])


def test_splits_nothing_when_there_is_no_system_prompt():
    messages = [UserMessage("hi")]

    assert split_system_prompt(messages) == (None, [UserMessage("hi")])
