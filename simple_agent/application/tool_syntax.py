from dataclasses import dataclass
from typing import Protocol

from simple_agent.application.tool_library import Tool, UnboundToolCall


@dataclass
class RawAssistantTurn:
    message: str
    tool_calls: list[UnboundToolCall]


class ToolSyntax(Protocol):
    def render_documentation(self, tool: Tool) -> str: ...

    def _format_example(self, example: object, tool: Tool) -> str: ...

    def parse(self, text: str) -> RawAssistantTurn: ...
