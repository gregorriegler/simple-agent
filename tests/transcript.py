"""How a tool call reads in a test transcript: one line of command text."""

from simple_agent.application.tool_library import ToolCall, call_body, call_header
from simple_agent.tools.all_tools import TOOL_DECLARATIONS


def describe_call(call: ToolCall) -> str:
    header = call_header(call, TOOL_DECLARATIONS)
    body = call_body(call, TOOL_DECLARATIONS)
    return " ".join(part for part in (header, body) if part)
