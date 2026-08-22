from simple_agent.application.tool_library import RawToolCall, Tool, ToolArgument

_TYPE_MAP = {
    "string": "STRING",
    "integer": "INTEGER",
    "number": "NUMBER",
    "boolean": "BOOLEAN",
}


def to_function_declarations(tools: list[Tool]) -> list[dict]:
    return [_declaration(tool) for tool in tools]


def _declaration(tool: Tool) -> dict:
    arguments = list(tool.arguments.all)
    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": {
            "type": "OBJECT",
            "properties": {arg.name: _property(arg) for arg in arguments},
            "required": [arg.name for arg in arguments if arg.required],
        },
    }


def _property(arg: ToolArgument) -> dict:
    return {"type": _TYPE_MAP.get(arg.type, "STRING"), "description": arg.description}


def to_raw_tool_calls(steps: list[dict], tools: list[Tool]) -> list[RawToolCall]:
    tools_by_name = {tool.name: tool for tool in tools}
    return [
        _raw_tool_call(step, tools_by_name.get(step.get("name")))
        for step in steps
        if step.get("type") == "function_call"
    ]


def _raw_tool_call(step: dict, tool: Tool | None) -> RawToolCall:
    name = step.get("name", "")
    arguments = step.get("arguments") or {}
    if tool is None:
        joined = " ".join(str(value) for value in arguments.values())
        return RawToolCall(name=name, arguments=joined, body="")

    header = " ".join(
        str(arguments[arg.name])
        for arg in tool.arguments.header
        if arg.name in arguments
    )
    body = ""
    if tool.arguments.body and tool.arguments.body.name in arguments:
        body = str(arguments[tool.arguments.body.name])
    return RawToolCall(name=name, arguments=header, body=body)
