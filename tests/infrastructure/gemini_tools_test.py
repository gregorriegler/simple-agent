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


def function_call(name, arguments, call_id=""):
    step = {"type": "function_call", "name": name, "arguments": arguments}
    if call_id:
        step["id"] = call_id
    return step


def test_reads_a_function_call_into_a_raw_tool_call_carrying_the_dict():
    calls = to_raw_tool_calls([function_call("bash", {"command": "ls -la"})])

    assert calls == [
        RawToolCall(name="bash", arguments="", named_arguments={"command": "ls -la"})
    ]


def test_leaves_the_positional_text_and_body_to_the_text_protocol():
    calls = to_raw_tool_calls(
        [function_call("create-file", {"filename": "a.txt", "content": "hello"})]
    )

    assert calls[0].arguments == ""
    assert calls[0].body == ""
    assert calls[0].named_arguments == {"filename": "a.txt", "content": "hello"}


def test_ignores_non_function_call_steps():
    calls = to_raw_tool_calls(
        [
            {"type": "model_output", "content": [{"type": "text", "text": "hi"}]},
            function_call("bash", {"command": "ls"}),
        ]
    )

    assert [call.name for call in calls] == ["bash"]


def test_captures_the_preceding_thought_signature_on_the_call():
    calls = to_raw_tool_calls(
        [
            {"type": "thought", "signature": "SIG"},
            function_call("bash", {"command": "ls"}),
        ]
    )

    assert calls[0].thought_signature == "SIG"


def test_reads_multiple_function_calls():
    calls = to_raw_tool_calls(
        [
            function_call("bash", {"command": "ls"}),
            function_call("bash", {"command": "pwd"}),
        ]
    )

    assert [call.named_arguments for call in calls] == [
        {"command": "ls"},
        {"command": "pwd"},
    ]


def test_keeps_the_native_call_id_on_the_call():
    calls = to_raw_tool_calls([function_call("bash", {"command": "ls"}, "fc_42")])

    assert calls[0].native_id == "fc_42"


def test_declares_a_bool_argument_as_a_json_boolean():
    subagent = tool(
        "subagent",
        "",
        ToolArguments(
            header=[ToolArgument(name="--async", type="bool", description="")]
        ),
    )

    declaration = to_function_declarations([subagent])[0]

    assert declaration["parameters"]["properties"]["--async"]["type"] == "boolean"
