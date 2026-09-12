import pytest

from simple_agent.application.tool_library import (
    ToolArgument,
    ToolArguments,
    ToolCall,
    ToolInvocation,
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


def test_a_flag_coerces_a_json_boolean_or_its_text_spellings():
    def flag(value):
        return ToolArgument(name="f", description="", type="bool").coerce(value)

    assert flag(True) is True
    assert flag("true") is True
    assert flag("True") is True
    assert flag("1") is True
    assert flag(False) is False
    assert flag("false") is False
    assert flag("") is False


def test_a_call_is_data_and_does_not_bind_itself():
    assert not hasattr(ToolCall("cat"), "bind")


def test_declared_arguments_coerce_values_to_their_declared_types():
    cat = ToolArguments(
        header=[
            ToolArgument(name="filename", description=""),
            ToolArgument(name="with_line_numbers", description="", type="bool"),
        ]
    )

    def bound(named):
        return cat.coerce(named)

    assert bound({"filename": 42, "with_line_numbers": "true"}) == {
        "filename": "42",
        "with_line_numbers": True,
    }
    assert bound({"filename": "f", "with_line_numbers": "false"}) == {
        "filename": "f",
        "with_line_numbers": False,
    }
    assert bound({"filename": "f"}) == {"filename": "f"}


def test_renders_a_header_quoting_values_with_spaces_and_true_flags_by_name():
    arguments = ToolArguments(
        header=[
            ToolArgument(name="agenttype", description=""),
            ToolArgument(name="task", description=""),
            ToolArgument(name="--async", description="", type="bool"),
        ]
    )
    named = {"agenttype": "coding", "task": "say hello", "--async": True}

    assert arguments.render_header(named) == "coding say hello --async"
    assert arguments.render_header({**named, "--async": False}) == "coding say hello"
    assert arguments.render_header({**named, "agenttype": "a b"}) == (
        "'a b' say hello --async"
    )


def test_renders_a_lone_positional_argument_as_written():
    arguments = ToolArguments(header=[ToolArgument(name="command", description="")])

    assert arguments.render_header({"command": "rg 'main\\(' -g '*.py'"}) == (
        "rg 'main\\(' -g '*.py'"
    )


def test_renders_the_body_value_and_nothing_without_a_body_argument():
    with_body = ToolArguments(body=ToolArgument(name="content", description=""))
    without = ToolArguments(header=[ToolArgument(name="command", description="")])

    assert with_body.render_body({"content": "line1\nline2"}) == "line1\nline2"
    assert without.render_body({"command": "ls"}) == ""


def test_a_windows_path_with_a_space_survives_rendering():
    arguments = ToolArguments(
        header=[
            ToolArgument(name="filename", description=""),
            ToolArgument(name="range", description="", required=False),
        ]
    )

    assert arguments.render_header({"filename": "C:\\Users\\me\\my notes.txt"}) == (
        "'C:\\Users\\me\\my notes.txt'"
    )


@pytest.mark.asyncio
async def test_an_invocation_executes_its_call_against_its_tool():
    class Echo:
        async def execute(self, call):
            return f"ran {call.name} with {call.named_arguments}"

    invocation = ToolInvocation(ToolCall("echo", {"text": "hi"}), Echo())

    assert await invocation.execute() == "ran echo with {'text': 'hi'}"
    assert invocation.name == "echo"


def test_an_integer_argument_coerces_a_number_or_its_text_to_an_int():
    def integer(value):
        return ToolArgument(name="n", description="", type="int").coerce(value)

    assert integer(3) == 3
    assert integer("3") == 3
    assert integer(3.0) == 3
    assert isinstance(integer("3"), int)


def test_a_number_argument_coerces_a_number_or_its_text_to_a_float():
    def number(value):
        return ToolArgument(name="x", description="", type="float").coerce(value)

    assert number(2.5) == 2.5
    assert number("2.5") == 2.5
    assert number(2) == 2.0
    assert isinstance(number(2), float)


def test_a_value_that_is_not_a_number_stays_text_under_a_numeric_type():
    integer = ToolArgument(name="n", description="", type="integer")
    number = ToolArgument(name="x", description="", type="number")

    assert integer.coerce("many") == "many"
    assert number.coerce("some") == "some"
