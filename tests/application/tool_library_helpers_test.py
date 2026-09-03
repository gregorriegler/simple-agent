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


def test_tool_arguments_splits_header_into_flags_and_positional():
    task = ToolArgument(name="task", description="")
    flag = ToolArgument(name="--async", description="", type="bool")
    arguments = ToolArguments(header=[task, flag])

    assert arguments.flags == [flag]
    assert arguments.positional == [task]


def test_a_lone_positional_argument_takes_the_whole_header_text():
    arguments = ToolArguments(header=[ToolArgument(name="command", description="")])

    assert arguments.single_positional is arguments["command"]


def test_no_single_positional_when_a_flag_shares_the_header():
    arguments = ToolArguments(
        header=[
            ToolArgument(name="command", description=""),
            ToolArgument(name="--verbose", description="", type="bool"),
        ]
    )

    assert arguments.single_positional is None
