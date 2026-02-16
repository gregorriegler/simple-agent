from dataclasses import dataclass

from simple_agent.application.tool_library import ToolLibrary


@dataclass
class Brain:
    name: str
    system_prompt: str
    tools: ToolLibrary
    model_name: str | None
