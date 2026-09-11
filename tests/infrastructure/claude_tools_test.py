from types import SimpleNamespace

import pytest

from simple_agent.application.tool_library import (
    ToolArgument,
    ToolArguments,
    ToolCall,
)
from simple_agent.infrastructure.claude.claude_tools import (
    UndeclaredTool,
    to_tool_calls,
    to_tools,
)


def tool(name, description, arguments):
    return SimpleNamespace(name=name, description=description, arguments=arguments)


def tool_use(name, arguments, block_id="toolu_1"):
    return {"type": "tool_use", "id": block_id, "name": name, "input": arguments}


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


def test_declares_a_tool_with_its_input_schema():
    assert to_tools([BASH]) == [
        {
            "name": "bash",
            "description": "Execute bash commands",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command"}
                },
                "required": ["command"],
            },
        }
    ]


def test_declares_a_bool_argument_as_a_json_boolean():
    properties = to_tools([CAT])[0]["input_schema"]["properties"]

    assert properties["with_line_numbers"]["type"] == "boolean"


def test_reads_a_tool_use_block_into_a_call_bound_to_its_tool():
    content = [
        {"type": "text", "text": "Let me look."},
        tool_use("bash", {"command": "ls -la"}, "toolu_abc"),
    ]

    calls = to_tool_calls(content, TOOLS)

    assert calls == [
        ToolCall(
            "bash", {"command": "ls -la"}, provider_state={"native_id": "toolu_abc"}
        )
    ]


def test_a_call_read_from_claude_carries_typed_arguments():
    content = [tool_use("cat", {"filename": 42, "with_line_numbers": "true"})]

    calls = to_tool_calls(content, TOOLS)

    assert calls[0].named_arguments == {"filename": "42", "with_line_numbers": True}


def test_a_call_to_an_undeclared_tool_is_refused():
    with pytest.raises(UndeclaredTool, match="rm"):
        to_tool_calls([tool_use("rm", {"path": "/"})], TOOLS)


def test_missing_input_reads_as_no_arguments():
    calls = to_tool_calls(
        [{"type": "tool_use", "id": "toolu_1", "name": "bash"}], TOOLS
    )

    assert calls[0].named_arguments == {}
