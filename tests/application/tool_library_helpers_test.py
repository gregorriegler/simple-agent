import pytest

from simple_agent.application.tool_library import ParsedTool, RawToolCall, ToolArgument, ToolArguments


def test_parsed_tool_cancelled_message_includes_header():
    raw_call = RawToolCall(name="tool", arguments="arg")
    parsed = ParsedTool(raw_call, tool_instance=None)

    message = parsed.cancelled_message()

    assert "Result of" in message
    assert "CANCELLED" in message


def test_tool_arguments_supports_len_and_getitem_by_name():
    arguments = ToolArguments(header=[ToolArgument(name="path", description="Path")])

    assert len(arguments) == 1
    assert arguments["path"].description == "Path"


def test_tool_arguments_getitem_raises_for_unknown_name():
    arguments = ToolArguments(header=[ToolArgument(name="path", description="Path")])

    with pytest.raises(KeyError, match="Argument 'missing' not found"):
        arguments["missing"]
