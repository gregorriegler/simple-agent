from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.llm import LLMResponse, TokenUsage

_SYNTAX = EmojiBracketToolSyntax()


def emoji_response(
    content: str, model: str, usage: TokenUsage | None, thought: str = ""
) -> LLMResponse:
    """
    Build an LLMResponse from an emoji-protocol text completion.

    The adapter owns parsing: the emoji tool calls are extracted into
    structured tool_calls and the surrounding prose becomes the message,
    while content keeps the raw text for history and round-trip.
    """
    raw_turn = _SYNTAX.parse(content)
    return LLMResponse(
        answer=content,
        tool_calls=raw_turn.tool_calls,
        message=raw_turn.message,
        model=model,
        usage=usage,
        thought=thought,
    )
