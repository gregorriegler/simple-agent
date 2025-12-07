from simple_agent.application.tool_syntax import ParsedMessage, ToolSyntax


def parse_tool_calls(text: str, syntax: ToolSyntax) -> ParsedMessage:
    return syntax.parse(text)
