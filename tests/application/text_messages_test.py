from simple_agent.application.llm import AssistantTurnMessage, ToolResultMessage
from simple_agent.application.text_messages import to_text_messages
from simple_agent.application.tool_library import RawToolCall


def test_passes_plain_messages_through():
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
    ]

    assert to_text_messages(messages) == messages


def test_renders_a_tool_result_as_user_text():
    messages = [
        ToolResultMessage(RawToolCall(name="bash", arguments="sleep 5"), "done")
    ]

    assert to_text_messages(messages) == [
        {"role": "user", "content": "Result of 🛠️ bash sleep 5\ndone"}
    ]


def test_drops_structured_tool_calls_keeping_assistant_text():
    messages = [
        AssistantTurnMessage(
            "🐙 running it 🛠️[bash sleep 5 /]",
            [RawToolCall(name="bash", arguments="sleep 5")],
        )
    ]

    assert to_text_messages(messages) == [
        {"role": "assistant", "content": "🐙 running it 🛠️[bash sleep 5 /]"}
    ]


def test_renders_native_tool_calls_as_emoji_text():
    call = RawToolCall(
        name="cat",
        arguments="my notes.md true",
        named_arguments={"filename": "my notes.md", "with_line_numbers": "true"},
        native_id="fc_1",
    )
    messages = [AssistantTurnMessage("", [call])]

    assert to_text_messages(messages) == [
        {"role": "assistant", "content": "🛠️[cat my notes.md true /]"}
    ]


def test_renders_a_native_call_with_a_body_and_keeps_the_prose():
    call = RawToolCall(
        name="create-file",
        arguments="a.txt",
        body="hello",
        named_arguments={"filename": "a.txt", "content": "hello"},
    )
    messages = [AssistantTurnMessage("creating it", [call])]

    assert to_text_messages(messages) == [
        {
            "role": "assistant",
            "content": "creating it\n🛠️[create-file a.txt]\nhello\n🛠️[/end]",
        }
    ]
