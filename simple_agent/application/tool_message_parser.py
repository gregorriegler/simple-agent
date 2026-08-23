from simple_agent.application.tool_syntax import RawAssistantTurn, ToolSyntax


def parse_tool_calls(text: str, syntax: ToolSyntax) -> RawAssistantTurn:
    return syntax.parse(text)
