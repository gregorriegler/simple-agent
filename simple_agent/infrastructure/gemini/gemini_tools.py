from simple_agent.application.tool_library import RawToolCall, Tool, ToolArgument

_TYPES = {"string", "integer", "number", "boolean"}
_TYPE_ALIASES = {
    "bool": "boolean",
    "int": "integer",
    "float": "number",
    "str": "string",
}


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
    arg_type = _TYPE_ALIASES.get(arg.type, arg.type)
    if arg_type not in _TYPES:
        arg_type = "string"
    return {"type": arg_type, "description": arg.description}


def to_raw_tool_calls(steps: list[dict]) -> list[RawToolCall]:
    """
    Read the function calls Gemini made. The call carries only what Gemini
    sent: its name, argument dict, id and thought signature. The positional
    text is a text-protocol concern and is rendered when the call is resolved.
    """
    calls: list[RawToolCall] = []
    pending_signature = ""
    for step in steps:
        step_type = step.get("type")
        if step_type == "thought":
            pending_signature = step.get("signature", "")
        elif step_type == "function_call":
            calls.append(
                RawToolCall(
                    name=step.get("name", ""),
                    arguments="",
                    named_arguments=step.get("arguments") or {},
                    native_id=step.get("id", ""),
                    thought_signature=pending_signature,
                )
            )
            pending_signature = ""
    return calls
