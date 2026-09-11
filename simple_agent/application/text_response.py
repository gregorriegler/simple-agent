from collections.abc import Mapping
from dataclasses import replace

from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.llm import LLM, ChatMessages, LLMResponse
from simple_agent.application.tool_library import RawToolCall, ToolDeclaration
from simple_agent.application.tool_syntax import ToolSyntax


def bind_emoji_calls(
    text: str, tools: Mapping[str, ToolDeclaration], syntax: ToolSyntax
) -> tuple[str, list[RawToolCall]]:
    """
    The message and the emoji calls in a text, each bound to the tool it
    names. A call to a tool not in the mapping leaves the whole text as the
    message with no calls.
    """
    turn = syntax.parse(text)
    bound: list[RawToolCall] = []
    for call in turn.tool_calls:
        tool = tools.get(call.name)
        if tool is None:
            return text, []
        bound.append(call.bind(tool))
    return turn.message, bound


class EmojiToolCallsLLM:
    """
    Binds the emoji tool calls in a text-only LLM's answer to the tools it
    was handed. A call to a tool it does not know leaves the whole answer
    as text, so the model's words reach the user unchanged.
    """

    def __init__(self, inner: LLM, tools: list[ToolDeclaration]):
        self._inner = inner
        self._tools = {tool.name: tool for tool in tools}
        self._syntax = EmojiBracketToolSyntax()

    @property
    def model(self) -> str:
        return self._inner.model

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        response = await self._inner.call_async(messages)
        message, calls = bind_emoji_calls(response.answer, self._tools, self._syntax)
        return replace(response, tool_calls=calls, message=message)
