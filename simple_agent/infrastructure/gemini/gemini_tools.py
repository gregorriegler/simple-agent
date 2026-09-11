from simple_agent.application.tool_library import (
    Tool,
    ToolArgument,
    ToolCall,
    ToolDeclarations,
)


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
    return {"type": arg.json_type, "description": arg.description}


def provider_state(native_id: str, thought_signature: str) -> dict[str, str]:
    state = {}
    if native_id:
        state["native_id"] = native_id
    if thought_signature:
        state["thought_signature"] = thought_signature
    return state


def native_id(call: ToolCall) -> str:
    return call.provider_state.get("native_id", "")


def thought_signature(call: ToolCall) -> str:
    return call.provider_state.get("thought_signature", "")


class UndeclaredTool(Exception):
    """Gemini called a function it was never declared."""


def to_tool_calls(steps: list[dict], tools: ToolDeclarations) -> list[ToolCall]:
    """
    Read the function calls Gemini made, each bound to the tool it names:
    the argument dict typed per the declaration, with Gemini's id and
    thought signature.
    """
    calls: list[ToolCall] = []
    pending_signature = ""
    for step in steps:
        step_type = step.get("type")
        if step_type == "thought":
            pending_signature = step.get("signature", "")
        elif step_type == "function_call":
            name = step.get("name", "")
            tool = tools.get(name)
            if tool is None:
                raise UndeclaredTool(f"Gemini called an undeclared tool: {name!r}")
            calls.append(
                ToolCall(
                    name=name,
                    named_arguments=tool.arguments.coerce(step.get("arguments") or {}),
                    provider_state=provider_state(
                        step.get("id", ""), pending_signature
                    ),
                )
            )
            pending_signature = ""
    return calls
