from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.tool_library import RawToolCall, Tool, ToolArgument

_SYNTAX = EmojiBracketToolSyntax()

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
            call.native_id = step.get("id", "")
            pending_signature = ""
            calls.append(call)
    return calls


def _raw_tool_call(step: dict, tool: Tool | None) -> RawToolCall:
    name = step.get("name", "")
    arguments = step.get("arguments") or {}
    if tool is None:
        joined = " ".join(str(value) for value in arguments.values())
        return RawToolCall(
            name=name, arguments=joined, body="", named_arguments=arguments
        )

    body = ""
    if tool.arguments.body and tool.arguments.body.name in arguments:
        body = str(arguments[tool.arguments.body.name])
    return RawToolCall(
        name=name,
        arguments=_SYNTAX.render_header(arguments, tool),
        body=body,
        named_arguments=arguments,
    )
