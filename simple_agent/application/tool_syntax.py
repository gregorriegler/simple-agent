from dataclasses import dataclass
from typing import Protocol, List

from simple_agent.application.tool_library import Tool, RawToolCall


@dataclass
class ParsedMessage:
    message: str
    tool_calls: List[RawToolCall]


class ToolSyntax(Protocol):
    def render_documentation(self, tool: Tool) -> str: ...

    def parse(self, text: str) -> ParsedMessage: ...
