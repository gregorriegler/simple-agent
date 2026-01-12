from simple_agent.application.agent_id import AgentId
from simple_agent.application.user_input import UserInput


class NonInteractiveUserInput(UserInput):
    async def read_async(self, agent_id: AgentId) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def close(self) -> None:
        pass
