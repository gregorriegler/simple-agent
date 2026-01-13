from .agent_id import AgentId
from .user_input import UserInput


class Input:
    def __init__(self, user_input: UserInput):
        self.user_input = user_input
        self._stack: list[str] = []

    def stack(self, message: str):
        self._stack.append(message)

    def has_stacked_messages(self) -> bool:
        return bool(self._stack)

    async def read_async(self, agent_id: AgentId | None = None) -> str:
        if self._stack:
            return self._stack.pop()
        return await self.user_input.read_async(agent_id=agent_id)

    def escape_requested(self) -> bool:
        return self.user_input.escape_requested()
