from typing import Protocol

from simple_agent.application.tool_library import ToolLibrary


class SystemPrompt(Protocol):

    def __call__(self, system_prompt_md: str, tool_library: ToolLibrary) -> str:
        ...
