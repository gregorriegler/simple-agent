from typing import Protocol, List, Optional

from simple_agent.application.tool_result import ToolResult


class ParsedTool(Protocol):
    arguments: str | None
    tool_instance: object


class ToolLibrary(Protocol):
    tools: List

    def get_tool_info(self, tool_name: str | None = None) -> str:
        ...

    def parse_tool(self, text: str) -> Optional[ParsedTool]:
        ...

    def execute_parsed_tool(self, parsed_tool: ParsedTool) -> ToolResult:
        ...
