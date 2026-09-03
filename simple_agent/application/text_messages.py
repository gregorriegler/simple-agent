from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.llm import ChatMessages

_SYNTAX = EmojiBracketToolSyntax()


def to_text_messages(messages: ChatMessages) -> ChatMessages:
    """
    Flatten structured tool turns into plain {role, content} text messages.

    Adapters that speak the emoji text protocol call this so a tool result
    becomes 'Result of ...' user text and an assistant turn carries its calls
    as emoji text: turns made under the text protocol already do, turns made
    natively get their calls rendered.
    """
    return [to_text_message(message) for message in messages]


def to_text_message(message: dict) -> dict:
    role = message.get("role", "")
    content = message.get("content", "")
    if role == "tool":
        return {
            "role": "user",
            "content": _SYNTAX.render_result(message["call"], content),
        }
    if role == "assistant":
        return {"role": role, "content": _with_calls_as_text(content, message)}
    return {"role": role, "content": content}


def _with_calls_as_text(content: str, message: dict) -> str:
    tool_calls = message.get("tool_calls") or []
    if not tool_calls or _SYNTAX.contains_call(content):
        return content
    rendered = "\n".join(_SYNTAX.render_call(call) for call in tool_calls)
    return f"{content}\n{rendered}" if content else rendered
