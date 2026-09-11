from simple_agent.application.tool_library import (
    Tool,
    ToolArgument,
    ToolCall,
    ToolDeclarations,
)


def to_tools(tools: list[Tool]) -> list[dict]:
    return [_tool(tool) for tool in tools]


def _tool(tool: Tool) -> dict:
    arguments = list(tool.arguments.all)
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": {
            "type": "object",
            "properties": {arg.name: _property(arg) for arg in arguments},
            "required": [arg.name for arg in arguments if arg.required],
        },
    }


def _property(arg: ToolArgument) -> dict:
    return {"type": arg.json_type, "description": arg.description}


def provider_state(native_id: str) -> dict[str, str]:
    return {"native_id": native_id} if native_id else {}


def native_id(call: ToolCall) -> str:
    return call.provider_state.get("native_id", "")


class UndeclaredTool(Exception):
    """Claude called a tool it was never declared."""


def to_tool_calls(content: list[dict], tools: ToolDeclarations) -> list[ToolCall]:
    """
    Read the tool_use blocks of a message's content, each bound to the
    tool it names: the input dict typed per the declaration, with Claude's
    block id.
    """
    calls: list[ToolCall] = []
    for block in content:
        if block.get("type") != "tool_use":
            continue
        name = block.get("name", "")
        tool = tools.get(name)
        if tool is None:
            raise UndeclaredTool(f"Claude called an undeclared tool: {name!r}")
        calls.append(
            ToolCall(
                name=name,
                named_arguments=tool.arguments.coerce(block.get("input") or {}),
                provider_state=provider_state(block.get("id", "")),
            )
        )
    return calls
