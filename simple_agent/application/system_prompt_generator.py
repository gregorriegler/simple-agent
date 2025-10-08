from typing import Protocol

from simple_agent.application.tool_library_protocol import ToolLibrary


class SystemPrompt(Protocol):

    def __call__(self, tool_library: ToolLibrary) -> str:
        ...
