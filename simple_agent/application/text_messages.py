from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.llm import (
    AssistantMessage,
    ChatMessage,
    ChatMessages,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.tool_library import RawToolCall

_SYNTAX = EmojiBracketToolSyntax()


def to_text_messages(messages: ChatMessages) -> list[dict[str, str]]:
    """
    Flatten structured tool turns into plain {role, content} wire messages.

    Adapters that speak the emoji text protocol call this so a tool result
    becomes 'Result of ...' user text and an assistant turn carries its calls
    as emoji text: turns made under the text protocol already do, turns made
    natively get their calls rendered.
    """
    return [_wire_message(to_text_turn(message)) for message in messages]


def split_system_prompt(messages: ChatMessages) -> tuple[str | None, ChatMessages]:
    """Take a leading system message off the conversation, if there is one."""
    if messages and isinstance(messages[0], SystemMessage):
        return messages[0].content, list(messages[1:])
    return None, list(messages)


def to_text_turn(
    message: ChatMessage,
) -> SystemMessage | UserMessage | AssistantMessage:
    if isinstance(message, ToolResultMessage):
        return UserMessage(_SYNTAX.render_result(message.call, message.content))
    if isinstance(message, AssistantMessage):
        return AssistantMessage(
            _with_calls_as_text(message.content, message.tool_calls)
        )
    return message


def _wire_message(
    message: SystemMessage | UserMessage | AssistantMessage,
) -> dict[str, str]:
    if isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    if isinstance(message, UserMessage):
        return {"role": "user", "content": message.content}
    return {"role": "assistant", "content": message.content}


def _with_calls_as_text(content: str, tool_calls: list[RawToolCall]) -> str:
    if not tool_calls or _SYNTAX.contains_call(content):
        return content
    rendered = "\n".join(_SYNTAX.render_call(call) for call in tool_calls)
    return f"{content}\n{rendered}" if content else rendered
