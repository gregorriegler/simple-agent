from types import SimpleNamespace

from simple_agent.application.tool_library import (
    RawToolCall,
    ToolArgument,
    ToolArguments,
)
from simple_agent.infrastructure.gemini.gemini_tools import (
    to_function_declarations,
    to_raw_tool_calls,
)


def tool(name, description, arguments):
    return SimpleNamespace(name=name, description=description, arguments=arguments)


def test_maps_a_tool_with_a_required_argument():
    bash = tool(
        "bash",
        "Execute bash commands",
        ToolArguments(
            header=[
                ToolArgument(
                    name="command",
                    description="The bash command to execute",
                    required=True,
                )
            ]
        ),
    )

    assert to_function_declarations([bash]) == [
        {
            "type": "function",
            "name": "bash",
            "description": "Execute bash commands",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute",
                    }
                },
                "required": ["command"],
            },
        }
    ]


def test_optional_arguments_are_not_required():
    cat = tool(
        "cat",
        "Display file contents",
        ToolArguments(
            header=[
                ToolArgument(name="filename", description="Path", required=True),
                ToolArgument(name="line_range", description="Range", required=False),
            ]
        ),
    )

    declaration = to_function_declarations([cat])[0]

    assert set(declaration["parameters"]["properties"]) == {"filename", "line_range"}
    assert declaration["parameters"]["required"] == ["filename"]


def test_body_argument_is_included_as_a_property():
    create_file = tool(
        "create-file",
        "Create a file",
        ToolArguments(
            header=[ToolArgument(name="filename", description="Path", required=True)],
            body=ToolArgument(name="content", description="File body", required=True),
        ),
    )

    properties = to_function_declarations([create_file])[0]["parameters"]["properties"]

    assert properties["content"] == {"type": "string", "description": "File body"}


def test_tool_without_arguments_has_empty_properties():
    ls = tool("ls", "List directory", ToolArguments())

    assert to_function_declarations([ls])[0]["parameters"] == {
        "type": "object",
        "properties": {},
        "required": [],
    }


def function_call(name, arguments):
    return {"type": "function_call", "name": name, "arguments": arguments}


def test_reads_a_single_argument_function_call_into_a_raw_tool_call():
    bash = tool(
        "bash",
        "",
        ToolArguments(header=[ToolArgument(name="command", description="")]),
    )

    calls = to_raw_tool_calls([function_call("bash", {"command": "ls -la"})], [bash])

    assert calls == [RawToolCall(name="bash", arguments="ls -la", body="")]


def test_joins_multiple_arguments_in_declared_order():
    cat = tool(
        "cat",
        "",
        ToolArguments(
            header=[
                ToolArgument(name="filename", description=""),
                ToolArgument(name="line_range", description="", required=False),
            ]
        ),
    )

    calls = to_raw_tool_calls(
        [function_call("cat", {"line_range": "1-20", "filename": "x.py"})], [cat]
    )

    assert calls == [RawToolCall(name="cat", arguments="x.py 1-20", body="")]


def test_body_argument_becomes_the_body():
    create_file = tool(
        "create-file",
        "",
        ToolArguments(
            header=[ToolArgument(name="filename", description="")],
            body=ToolArgument(name="content", description=""),
        ),
    )

    calls = to_raw_tool_calls(
        [function_call("create-file", {"filename": "a.txt", "content": "hello"})],
        [create_file],
    )

    assert calls == [RawToolCall(name="create-file", arguments="a.txt", body="hello")]


def test_ignores_non_function_call_steps():
    calls = to_raw_tool_calls(
        [
            {"type": "model_output", "content": [{"type": "text", "text": "hi"}]},
            {"type": "thought", "signature": "x"},
        ],
        [],
    )

    assert calls == []


def test_reads_multiple_function_calls():
    bash = tool(
        "bash",
        "",
        ToolArguments(header=[ToolArgument(name="command", description="")]),
    )

    calls = to_raw_tool_calls(
        [
            function_call("bash", {"command": "ls"}),
            function_call("bash", {"command": "pwd"}),
        ],
        [bash],
    )

    assert [c.arguments for c in calls] == ["ls", "pwd"]
