from typing import Protocol, List

from simple_agent.application.tool_result import ToolResult
from simple_agent.tools.tool_library import ParsedTool


class ToolLibrary(Protocol):
    tools: List

    def get_tool_info(self, tool_name: str | None = None) -> str:
        ...

    def parse_tool(self, text: str) -> ParsedTool | None:
        ...

    def execute_parsed_tool(self, parsed_tool: ParsedTool) -> ToolResult:
        ...
