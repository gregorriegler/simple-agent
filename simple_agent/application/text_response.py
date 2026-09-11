from collections.abc import Mapping
from dataclasses import replace

from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.llm import LLM, ChatMessages, LLMResponse
from simple_agent.application.text_messages import to_text_turn
from simple_agent.application.tool_library import ToolCall, ToolDeclaration
from simple_agent.application.tool_syntax import ToolSyntax


def bind_emoji_calls(
    text: str, tools: Mapping[str, ToolDeclaration], syntax: ToolSyntax
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
        message, calls = bind_emoji_calls(response.answer, self._tools, self._syntax)
        return replace(response, tool_calls=calls, message=message)
