from typing import Protocol, TYPE_CHECKING

from simple_agent.application.tool_library import ToolLibrary

if TYPE_CHECKING:
    from simple_agent.application.agent_factory import ToolContext


class ToolLibraryFactory(Protocol):
    def create(
        self,
        tool_context: "ToolContext"
    ) -> ToolLibrary:
        ...
