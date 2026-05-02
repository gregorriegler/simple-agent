from dataclasses import dataclass

from simple_agent.application.llm import LLM
from simple_agent.application.tool_library import ToolLibrary


@dataclass
class Brain:
    name: str
    system_prompt: str
    llm: LLM
    tools: ToolLibrary
