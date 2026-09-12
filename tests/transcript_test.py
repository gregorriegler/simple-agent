from simple_agent.application.llm import AssistantMessage, UserMessage
from simple_agent.application.tool_library import ToolCall
from tests.transcript import describe_call, render_messages


def test_a_call_reads_as_its_name_and_named_arguments():
    call = ToolCall("cat", {"filename": "my notes.md", "with_line_numbers": True})

    assert describe_call(call) == 'cat filename="my notes.md" with_line_numbers=true'


def test_a_multi_line_value_stays_on_the_call_line():
    call = ToolCall("create-file", {"filename": "a", "content": "one\ntwo"})

    assert describe_call(call) == 'create-file filename="a" content="one\\ntwo"'


def test_a_call_without_arguments_is_just_its_name():
    assert describe_call(ToolCall("ls")) == "ls"


def test_an_assistant_turn_lists_its_calls_indented_under_its_words():
    messages = [
        UserMessage("hi"),
        AssistantMessage("Hello!", [ToolCall("complete-task", {"summary": "done"})]),
    ]

    assert render_messages(messages) == (
        'user: hi\nassistant: Hello!\n  complete-task summary="done"'
    )
