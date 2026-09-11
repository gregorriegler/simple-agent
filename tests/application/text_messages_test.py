import pytest

from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.llm import (
    AssistantMessage,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.text_messages import (
    split_system_prompt,
    to_text_messages,
    to_wire_messages,
)
from simple_agent.application.tool_library import ToolCall
from simple_agent.tools.bash_tool import BashTool
from simple_agent.tools.cat_tool import CatTool
from simple_agent.tools.create_file_tool import CreateFileTool

SYNTAX = EmojiBracketToolSyntax(
    {"cat": CatTool(), "create-file": CreateFileTool(), "bash": BashTool()}
)


def test_renders_plain_messages_as_role_keyed_dicts():
    messages = [SystemMessage("sys"), UserMessage("hi")]

    assert to_wire_messages(messages) == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
    ]


def test_splits_a_leading_system_prompt_off_the_history():
    messages = [SystemMessage("sys"), UserMessage("hi")]

    assert split_system_prompt(messages) == ("sys", [UserMessage("hi")])


def test_splits_nothing_when_there_is_no_system_prompt():
    messages = [UserMessage("hi")]

    assert split_system_prompt(messages) == (None, [UserMessage("hi")])


def test_renders_a_tool_result_as_user_text():
    messages = [ToolResultMessage(ToolCall("bash", {"command": "sleep 5"}), "done")]

    assert to_text_messages(messages, SYNTAX) == [
        {"role": "user", "content": "Result of 🛠️ bash sleep 5\ndone"}
    ]


def test_drops_structured_tool_calls_keeping_assistant_text():
    messages = [
        AssistantMessage(
            "🐙 running it 🛠️[bash sleep 5 /]",
            [ToolCall("bash", {"command": "sleep 5"})],
        )
    ]

    assert to_text_messages(messages, SYNTAX) == [
        {"role": "assistant", "content": "🐙 running it 🛠️[bash sleep 5 /]"}
    ]


def test_a_tool_turn_has_no_wire_shape_until_rendered_to_text():
    messages = [ToolResultMessage(ToolCall("bash", {"command": "ls"}), "done")]

    with pytest.raises(TypeError, match="render it to text first"):
        to_wire_messages(messages)


def test_renders_native_tool_calls_as_emoji_text():
    call = ToolCall(
        "cat",
        {"filename": "my notes.md", "with_line_numbers": True},
        provider_state={"native_id": "fc_1"},
    )
    messages = [AssistantMessage("", [call])]

    assert to_text_messages(messages, SYNTAX) == [
        {"role": "assistant", "content": "🛠️[cat 'my notes.md' with_line_numbers /]"}
    ]


def test_renders_a_native_call_with_a_body_and_keeps_the_prose():
    call = ToolCall("create-file", {"filename": "a.txt", "content": "hello"})
    messages = [AssistantMessage("creating it", [call])]

    assert to_text_messages(messages, SYNTAX) == [
        {
            "role": "assistant",
            "content": "creating it\n🛠️[create-file a.txt]\nhello\n🛠️[/end]",
        }
    ]
