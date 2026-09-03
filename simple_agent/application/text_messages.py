from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.llm import (
    AssistantTurnMessage,
    ChatMessage,
    ChatMessages,
    ToolResultMessage,
)
from simple_agent.application.tool_library import RawToolCall

_SYNTAX = EmojiBracketToolSyntax()


def to_text_messages(messages: ChatMessages) -> list[dict[str, str]]:
    """
    Flatten structured tool turns into plain {role, content} text messages.

    Adapters that speak the emoji text protocol call this so a tool result
    becomes 'Result of ...' user text and an assistant turn carries its calls
    as emoji text: turns made under the text protocol already do, turns made
    natively get their calls rendered.
    """
    return [to_text_message(message) for message in messages]


def to_text_message(message: ChatMessage) -> dict[str, str]:
    if isinstance(message, ToolResultMessage):
        content = _SYNTAX.render_result(message.call, message.content)
        return {"role": "user", "content": content}
    if isinstance(message, AssistantTurnMessage):
        content = _with_calls_as_text(message.content, message.tool_calls)
        return {"role": "assistant", "content": content}
    return {"role": message.get("role", ""), "content": message.get("content", "")}


def _with_calls_as_text(content: str, tool_calls: list[RawToolCall]) -> str:
    if not tool_calls or _SYNTAX.contains_call(content):
        return content
    rendered = "\n".join(_SYNTAX.render_call(call) for call in tool_calls)
    return f"{content}\n{rendered}" if content else rendered
