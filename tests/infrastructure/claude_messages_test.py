import pytest

from simple_agent.application.llm import (
    AssistantMessage,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.tool_library import ToolCall
from simple_agent.infrastructure.claude.claude_messages import to_messages_api

CAT_CALL = ToolCall(
    "cat", {"filename": "my notes.md"}, provider_state={"native_id": "toolu_abc"}
)
LS_CALL = ToolCall("ls", {"path": "."}, provider_state={"native_id": "toolu_def"})


def test_renders_plain_turns_as_text_content():
    assert to_messages_api([UserMessage("hi"), AssistantMessage("hello")]) == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_an_assistant_turn_carries_its_calls_as_tool_use_blocks():
    assert to_messages_api([AssistantMessage("Let me look.", [CAT_CALL])]) == [
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Let me look."},
                {
                    "type": "tool_use",
                    "id": "toolu_abc",
                    "name": "cat",
                    "input": {"filename": "my notes.md"},
                },
            ],
        }
    ]


def test_a_call_without_text_has_no_text_block():
    content = to_messages_api([AssistantMessage("", [CAT_CALL])])[0]["content"]

    assert [block["type"] for block in content] == ["tool_use"]


def test_a_tool_result_answers_the_call_in_a_user_turn():
    assert to_messages_api([ToolResultMessage(CAT_CALL, "Hello world")]) == [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_abc",
                    "content": "Hello world",
                }
            ],
        }
    ]


def test_results_of_one_turn_share_a_single_user_message():
    messages = to_messages_api(
        [
            AssistantMessage("", [CAT_CALL, LS_CALL]),
            ToolResultMessage(CAT_CALL, "Hello world"),
            ToolResultMessage(LS_CALL, "my notes.md"),
            UserMessage("thanks"),
        ]
    )

    assert [m["role"] for m in messages] == ["assistant", "user", "user"]
    assert [b["tool_use_id"] for b in messages[1]["content"]] == [
        "toolu_abc",
        "toolu_def",
    ]


def test_an_empty_result_carries_no_content():
    block = to_messages_api([ToolResultMessage(CAT_CALL, "")])[0]["content"][0]

    assert block == {"type": "tool_result", "tool_use_id": "toolu_abc"}


def test_a_call_without_an_id_is_replayed_under_a_synthetic_one():
    call = ToolCall("cat", {"filename": "a.md"})
    other = ToolCall("ls", {"path": "."})

    messages = to_messages_api(
        [
            AssistantMessage("", [call, other]),
            ToolResultMessage(call, "A"),
            ToolResultMessage(other, "a.md"),
        ]
    )

    assert [b["id"] for b in messages[0]["content"]] == ["toolu_1", "toolu_2"]
    assert [b["tool_use_id"] for b in messages[1]["content"]] == [
        "toolu_1",
        "toolu_2",
    ]


def test_a_system_message_has_no_place_in_the_history():
    with pytest.raises(TypeError, match="system"):
        to_messages_api([SystemMessage("be brief")])
