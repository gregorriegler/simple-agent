from dataclasses import dataclass

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse
from simple_agent.application.tool_library import ToolLibrary


@dataclass
class Brain:
    name: str
    system_prompt: str
    llm: LLM
    tools: ToolLibrary

    async def respond(self, messages: ChatMessages) -> LLMResponse:
        return await self.llm.call_async(messages)
