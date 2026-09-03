import pytest

from simple_agent.application.tool_library import (
    RawToolCall,
    ToolArgument,
    ToolArguments,
)


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


def test_a_bool_argument_is_a_flag_under_either_spelling():
    assert ToolArgument(name="--async", description="", type="bool").is_flag
    assert ToolArgument(name="--async", description="", type="boolean").is_flag
    assert not ToolArgument(name="task", description="").is_flag


def test_json_type_normalises_python_spellings_and_falls_back_to_string():
    def json_type(declared):
        return ToolArgument(name="x", description="", type=declared).json_type

    assert json_type("bool") == "boolean"
    assert json_type("int") == "integer"
    assert json_type("float") == "number"
    assert json_type("str") == "string"
    assert json_type("boolean") == "boolean"
    assert json_type("path") == "string"


def test_a_flag_reads_true_from_a_json_boolean_or_its_text_spellings():
    def flag(value):
        return RawToolCall(name="t", arguments="", named_arguments={"f": value}).flag(
            "f"
        )

    assert flag(True)
    assert flag("true")
    assert flag("True")
    assert flag("1")
    assert not flag(False)
    assert not flag("false")
    assert not flag("")


def test_an_absent_flag_reads_false():
    assert not RawToolCall(name="t", arguments="").flag("f")
