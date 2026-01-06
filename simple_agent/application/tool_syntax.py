from dataclasses import dataclass
from typing import Protocol

from simple_agent.application.tool_library import RawToolCall, Tool


@dataclass
class ParsedMessage:
    message: str
    tool_calls: list[RawToolCall]


class ToolSyntax(Protocol):
    def render_documentation(self, tool: Tool) -> str: ...

    def parse(self, text: str) -> ParsedMessage: ...
