"""
The emoji text protocol around a text-only LLM, kept for the tests only:
the stub LLMs answer in emoji text, and this binds their calls the way the
adapters bind native ones.
"""

from collections.abc import Mapping
from dataclasses import replace

from simple_agent.application.llm import (
    LLM,
    AssistantMessage,
    ChatMessage,
    ChatMessages,
    LLMResponse,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.tool_library import (
    AssistantTurn,
    ToolCall,
    ToolDeclaration,
    ToolLibrary,
)
from tests.emoji_syntax import EmojiBracketToolSyntax

TextTurn = SystemMessage | UserMessage | AssistantMessage


def bind_emoji_calls(
    text: str, tools: Mapping[str, ToolDeclaration], syntax: EmojiBracketToolSyntax
) -> tuple[str, list[ToolCall]]:
    """
    The message and the emoji calls in a text, each bound to the tool it
    names. A call to a tool not in the mapping leaves the whole text as the
    message with no calls.
    """
    turn = syntax.parse(text)
    bound: list[ToolCall] = []
    for call in turn.tool_calls:
        tool = tools.get(call.name)
        if tool is None:
            return text, []
        bound.append(call.bind(tool))
    return turn.message, bound


def resolve_emoji(library: ToolLibrary, text: str) -> AssistantTurn:
    """Parse emoji text against a tool library and pair each call with its tool."""
    tools = {tool.name: tool for tool in library.tools}
    message, calls = bind_emoji_calls(text, tools, EmojiBracketToolSyntax(tools))
    return library.resolve_tool_calls(calls, message)


class EmojiToolCallsLLM:
    """
    The emoji text protocol around a text-only LLM: the history goes in as
    the text turns it would have been, and the emoji tool calls in the
    answer come out bound to the tools it was handed. A call to a tool it
    does not know leaves the whole answer as text, so the model's words
    reach the user unchanged.
    """

    def __init__(self, inner: LLM, tools: list[ToolDeclaration]):
        self._inner = inner
        self._tools = {tool.name: tool for tool in tools}
        self._syntax = EmojiBracketToolSyntax(self._tools)

    @property
    def model(self) -> str:
        return self._inner.model

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        history = [to_text_turn(message, self._syntax) for message in messages]
        response = await self._inner.call_async(history)
        if response.tool_calls:
            return response
        message, calls = bind_emoji_calls(response.answer, self._tools, self._syntax)
        return replace(response, tool_calls=calls, message=message)


class EmojiLLMProvider:
    """Hands one text LLM out under the emoji protocol, whatever model is asked for."""

    def __init__(self, llm: LLM):
        self._llm = llm

    def get(self, model_name: str | None = None, tools: list | None = None) -> LLM:
        return EmojiToolCallsLLM(self._llm, tools or [])

    def get_available_models(self) -> list[str]:
        return [self._llm.model]


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
