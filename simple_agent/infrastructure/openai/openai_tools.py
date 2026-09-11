import json

from simple_agent.application.tool_library import (
    Tool,
    ToolArgument,
    ToolCall,
    ToolDeclarations,
)


def to_tools(tools: list[Tool]) -> list[dict]:
    return [{"type": "function", "function": _function(tool)} for tool in tools]


def _function(tool: Tool) -> dict:
    arguments = list(tool.arguments.all)
    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": {
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
    """OpenAI called a function it was never declared."""


class MalformedArguments(Exception):
    """OpenAI's argument string for a call is not a JSON object."""


def to_tool_calls(message_calls: list[dict], tools: ToolDeclarations) -> list[ToolCall]:
    """
    Read the tool calls of a chat completion message, each bound to the
    tool it names: the JSON argument string decoded and typed per the
    declaration, with OpenAI's call id.
    """
    calls: list[ToolCall] = []
    for message_call in message_calls:
        function = message_call.get("function") or {}
        name = function.get("name", "")
        tool = tools.get(name)
        if tool is None:
            raise UndeclaredTool(f"OpenAI called an undeclared tool: {name!r}")
        arguments = _decode_arguments(name, function.get("arguments") or "{}")
        calls.append(
            ToolCall(
                name=name,
                named_arguments=tool.arguments.coerce(arguments),
                provider_state=provider_state(message_call.get("id", "")),
            )
        )
    return calls


def _decode_arguments(name: str, arguments: str) -> dict:
    try:
        decoded = json.loads(arguments)
    except json.JSONDecodeError as error:
        raise MalformedArguments(
            f"OpenAI called {name!r} with malformed arguments: {arguments!r}"
        ) from error
    if not isinstance(decoded, dict):
        raise MalformedArguments(
            f"OpenAI called {name!r} with non-object arguments: {arguments!r}"
        )
    return decoded
