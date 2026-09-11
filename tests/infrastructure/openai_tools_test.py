import json
from types import SimpleNamespace

import pytest

from simple_agent.application.tool_library import (
    ToolArgument,
    ToolArguments,
    ToolCall,
)
from simple_agent.infrastructure.openai.openai_tools import (
    MalformedArguments,
    UndeclaredTool,
    to_tool_calls,
    to_tools,
)


def tool(name, description, arguments):
    return SimpleNamespace(name=name, description=description, arguments=arguments)


def message_call(name, arguments, call_id="call_1"):
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }


BASH = tool(
    "bash",
    "Execute bash commands",
    ToolArguments(
        header=[
            ToolArgument(name="command", description="The bash command", required=True)
        ]
    ),
)
CAT = tool(
    "cat",
    "",
    ToolArguments(
        header=[
            ToolArgument(name="filename", description=""),
            ToolArgument(name="with_line_numbers", description="", type="bool"),
        ]
    ),
)
TOOLS = {"bash": BASH, "cat": CAT}


def test_declares_a_tool_as_a_chat_completion_function_tool():
    assert to_tools([BASH]) == [
        {
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Execute bash commands",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command",
                        }
                    },
                    "required": ["command"],
                },
            },
        }
    ]


def test_declares_a_bool_argument_as_a_json_boolean():
    properties = to_tools([CAT])[0]["function"]["parameters"]["properties"]

    assert properties["with_line_numbers"]["type"] == "boolean"


def test_reads_a_tool_call_into_a_call_bound_to_its_tool():
    calls = to_tool_calls(
        [message_call("bash", json.dumps({"command": "ls -la"}), "call_abc")], TOOLS
    )

    assert calls == [
        ToolCall(
            "bash", {"command": "ls -la"}, provider_state={"native_id": "call_abc"}
        )
    ]


def test_a_call_read_from_openai_carries_typed_arguments():
    arguments = json.dumps({"filename": 42, "with_line_numbers": "true"})

    calls = to_tool_calls([message_call("cat", arguments)], TOOLS)

    assert calls[0].named_arguments == {"filename": "42", "with_line_numbers": True}


def test_a_call_to_an_undeclared_tool_is_refused():
    with pytest.raises(UndeclaredTool, match="rm"):
        to_tool_calls([message_call("rm", json.dumps({"path": "/"}))], TOOLS)


def test_malformed_arguments_are_refused_with_the_tool_named():
    with pytest.raises(MalformedArguments, match="bash"):
        to_tool_calls([message_call("bash", '{"command": ')], TOOLS)


def test_empty_arguments_read_as_no_arguments():
    calls = to_tool_calls([message_call("bash", "")], TOOLS)

    assert calls[0].named_arguments == {}
