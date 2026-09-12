from .agent_id import AgentId
from .queued_user_input import QueuedUserInput
from .user_input import UserInput


class RoutedUserInput:
    """One keyboard channel per agent: a message goes to the agent it was typed for."""

    def __init__(self):
        self._channels: dict[AgentId, QueuedUserInput] = {}
        self._closed = False

    def for_agent(self, agent_id: AgentId) -> UserInput:
        return self._channel(agent_id)

    def submit_input(self, agent_id: AgentId, message: str) -> None:
        self._channel(agent_id).submit_input(message)

    def close(self) -> None:
        self._closed = True
        for channel in self._channels.values():
            channel.close()

    def _channel(self, agent_id: AgentId) -> QueuedUserInput:
        channel = self._channels.get(agent_id)
        if channel is None:
            channel = QueuedUserInput()
            if self._closed:
                channel.close()
            self._channels[agent_id] = channel
        return channel
