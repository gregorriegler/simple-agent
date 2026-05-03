from dataclasses import dataclass

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse
from simple_agent.application.tool_library import MessageAndParsedTools, ToolLibrary


@dataclass
class Brain:
    name: str
    system_prompt: str
    llm: LLM
    tools: ToolLibrary

    async def respond(
        self, messages: ChatMessages
    ) -> tuple[LLMResponse, MessageAndParsedTools]:
        response = await self.llm.call_async(messages)
        return response, self.tools.parse_message_and_tools(response.content)
