from simple_agent.application.tool_library import RawToolCall, Tool, ToolArgument

_TYPES = {"string", "integer", "number", "boolean"}


def to_function_declarations(tools: list[Tool]) -> list[dict]:
    return [_declaration(tool) for tool in tools]


def _declaration(tool: Tool) -> dict:
    arguments = list(tool.arguments.all)
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": {
            "type": "object",
            "properties": {arg.name: _property(arg) for arg in arguments},
            "required": [arg.name for arg in arguments if arg.required],
        },
    }


def _property(arg: ToolArgument) -> dict:
    arg_type = arg.type if arg.type in _TYPES else "string"
    return {"type": arg_type, "description": arg.description}


def to_raw_tool_calls(steps: list[dict], tools: list[Tool]) -> list[RawToolCall]:
    tools_by_name = {tool.name: tool for tool in tools}
    calls: list[RawToolCall] = []
    pending_signature = ""
    for step in steps:
        step_type = step.get("type")
        if step_type == "thought":
            pending_signature = step.get("signature", "")
        elif step_type == "function_call":
            call = _raw_tool_call(step, tools_by_name.get(step.get("name")))
            call.thought_signature = pending_signature
            pending_signature = ""
            calls.append(call)
    return calls


def to_native_arguments(raw_call: RawToolCall, tool: Tool | None) -> dict:
    """Reconstruct a native argument dict from a positional RawToolCall."""
    if tool is None:
        return {}
    header = list(tool.arguments.header)
    arguments: dict = {}
    if header:
        values = raw_call.arguments.split(None, len(header) - 1)
        for arg, value in zip(header, values, strict=False):
            arguments[arg.name] = value
    if tool.arguments.body and raw_call.body:
        arguments[tool.arguments.body.name] = raw_call.body
    return arguments


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
