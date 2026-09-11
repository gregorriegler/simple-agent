from simple_agent.application.llm import (
    AssistantMessage,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.text_messages import (
    split_system_prompt,
    to_text_messages,
)
from simple_agent.application.tool_library import ToolCall
from simple_agent.tools.cat_tool import CatTool
from simple_agent.tools.create_file_tool import CreateFileTool


def test_renders_plain_messages_as_role_keyed_dicts():
    messages = [SystemMessage("sys"), UserMessage("hi")]

    assert to_text_messages(messages) == [
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

    assert to_text_messages(messages) == [
        {"role": "user", "content": "Result of 🛠️ bash sleep 5\ndone"}
    ]


def test_drops_structured_tool_calls_keeping_assistant_text():
    messages = [
        AssistantMessage(
            "🐙 running it 🛠️[bash sleep 5 /]",
            [ToolCall("bash", {"command": "sleep 5"})],
        )
    ]

    assert to_text_messages(messages) == [
        {"role": "assistant", "content": "🐙 running it 🛠️[bash sleep 5 /]"}
    ]


def test_renders_native_tool_calls_as_emoji_text():
    call = ToolCall(
        "cat",
        {"filename": "my notes.md", "with_line_numbers": "true"},
        native_id="fc_1",
    ).bind(CatTool)
    messages = [AssistantMessage("", [call])]

    assert to_text_messages(messages) == [
        {"role": "assistant", "content": "🛠️[cat 'my notes.md' with_line_numbers /]"}
    ]


def test_renders_a_native_call_with_a_body_and_keeps_the_prose():
    call = ToolCall("create-file", {"filename": "a.txt", "content": "hello"}).bind(
        CreateFileTool
    )
    messages = [AssistantMessage("creating it", [call])]

    assert to_text_messages(messages) == [
        {
            "role": "assistant",
            "content": "creating it\n🛠️[create-file a.txt]\nhello\n🛠️[/end]",
        }
    ]
