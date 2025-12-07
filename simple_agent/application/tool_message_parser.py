from simple_agent.application.tool_syntax import ParsedMessage
from simple_agent.application.emoji_tool_syntax import EmojiToolSyntax

CURRENT_SYNTAX = EmojiToolSyntax()


def parse_tool_calls(text: str, syntax=None) -> ParsedMessage:
    if syntax is None:
        syntax = CURRENT_SYNTAX
    return syntax.parse(text)
