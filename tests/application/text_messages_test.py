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
        {
            "role": "tool",
            "call": RawToolCall(name="bash", arguments="sleep 5"),
            "content": "done",
        }
    ]

    assert to_text_messages(messages) == [
        {"role": "user", "content": "Result of 🛠️ bash sleep 5\ndone"}
    ]


def test_drops_structured_tool_calls_keeping_assistant_text():
    messages = [
        {
            "role": "assistant",
            "content": "🐙 running it 🛠️[bash sleep 5 /]",
            "tool_calls": [RawToolCall(name="bash", arguments="sleep 5")],
        }
    ]

    assert to_text_messages(messages) == [
        {"role": "assistant", "content": "🐙 running it 🛠️[bash sleep 5 /]"}
    ]
