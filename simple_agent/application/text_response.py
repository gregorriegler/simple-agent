from dataclasses import replace

from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.llm import LLM, ChatMessages, LLMResponse
from simple_agent.application.tool_library import RawToolCall, ToolDeclaration


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
        turn = self._syntax.parse(response.answer)
        bound: list[RawToolCall] = []
        for call in turn.tool_calls:
            tool = self._tools.get(call.name)
            if tool is None:
                return replace(response, tool_calls=[], message=response.answer)
            bound.append(call.bind(tool))
        return replace(response, tool_calls=bound, message=turn.message)
