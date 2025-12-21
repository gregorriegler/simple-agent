import pytest

from simple_agent.application.tool_library import ToolArgument, ToolArguments


def test_tool_arguments_supports_len_and_getitem_by_name():
    arguments = ToolArguments(header=[ToolArgument(name="path", description="Path")])

    assert len(arguments) == 1
    assert arguments["path"].description == "Path"


def test_tool_arguments_getitem_raises_for_unknown_name():
    arguments = ToolArguments(header=[ToolArgument(name="path", description="Path")])

    with pytest.raises(KeyError, match="Argument 'missing' not found"):
        arguments["missing"]
