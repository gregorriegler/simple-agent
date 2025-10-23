from typing import Protocol

from simple_agent.application.tool_library import ToolLibrary


class ToolLibraryFactory(Protocol):
    def create(
        self,
        tool_keys: list[str],
        subagent_context
    ) -> ToolLibrary:
        ...
