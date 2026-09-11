from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.llm import (
    AssistantMessage,
    ChatMessage,
    ChatMessages,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)

TextTurn = SystemMessage | UserMessage | AssistantMessage


def to_text_messages(
    messages: ChatMessages, syntax: EmojiBracketToolSyntax
) -> list[dict[str, str]]:
    """
    Flatten structured tool turns into plain {role, content} wire messages:
    a tool result becomes 'Result of ...' user text and an assistant turn
    carries its calls as emoji text, rendered through the syntax.
    """
    return to_wire_messages([to_text_turn(message, syntax) for message in messages])


def to_wire_messages(messages: ChatMessages) -> list[dict[str, str]]:
    """
    Plain {role, content} wire messages for text turns. A tool turn has no
    wire shape here; it must have been rendered to text first.
    """
    return [message.render(_WIRE) for message in messages]


def to_text_turn(message: ChatMessage, syntax: EmojiBracketToolSyntax) -> TextTurn:
    return message.render(_AsTextTurn(syntax))


def split_system_prompt(messages: ChatMessages) -> tuple[str | None, ChatMessages]:
    """Take a leading system message off the conversation, if there is one."""
    if messages and isinstance(messages[0], SystemMessage):
        return messages[0].content, list(messages[1:])
    return None, list(messages)


class _AsTextTurn:
    """Renders a tool turn as the emoji text it would have been."""

    def __init__(self, syntax: EmojiBracketToolSyntax) -> None:
        self._syntax = syntax

    def system(self, message: SystemMessage) -> TextTurn:
        return message

    def user(self, message: UserMessage) -> TextTurn:
        return message

    def assistant(self, message: AssistantMessage) -> TextTurn:
        content = message.content
        if message.tool_calls and not self._syntax.contains_call(content):
            calls = "\n".join(self._syntax.render_call(c) for c in message.tool_calls)
            content = f"{content}\n{calls}" if content else calls
        return AssistantMessage(content)

    def tool_result(self, message: ToolResultMessage) -> TextTurn:
        return UserMessage(self._syntax.render_result(message.call, message.content))


class _AsWireMessage:
    def system(self, message: SystemMessage) -> dict[str, str]:
        return {"role": "system", "content": message.content}

    def user(self, message: UserMessage) -> dict[str, str]:
        return {"role": "user", "content": message.content}

    def assistant(self, message: AssistantMessage) -> dict[str, str]:
        return {"role": "assistant", "content": message.content}

    def tool_result(self, message: ToolResultMessage) -> dict[str, str]:
        raise TypeError("a tool result has no wire shape; render it to text first")


_WIRE = _AsWireMessage()
