from simple_agent.application.agent_id import AgentId
from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.event_bus import EventBus
from simple_agent.application.events import (
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    UserPromptedEvent,
)
from simple_agent.application.llm import Messages
from simple_agent.application.session_storage import AgentMetadata, SessionStorage
from simple_agent.application.tool_message_parser import parse_tool_calls


class HistoryReplayer:
    def __init__(self, event_bus: EventBus, session_storage: SessionStorage):
        self._event_bus = event_bus
        self._session_storage = session_storage
        self._tool_syntax = EmojiBracketToolSyntax()

    def replay_all_agents(self, starting_agent_id: AgentId) -> None:
        self._replay_agent(starting_agent_id)

    def _replay_agent(self, agent_id: AgentId) -> None:
        messages = self._session_storage.load_messages(agent_id)
        if len(messages) == 0:
            return

        metadata = self._session_storage.load_metadata(agent_id)
        self._replay_messages(agent_id, messages, metadata)

    def _replay_messages(
        self, agent_id: AgentId, messages: Messages, metadata: AgentMetadata
    ) -> None:
        last_assistant_content = ""
        for message in messages.to_list():
            role = message.get("role")
            content = message.get("content", "")

            if role == "system":
                continue
            elif role == "user":
                self._event_bus.publish(
                    UserPromptedEvent(agent_id=agent_id, input_text=content)
                )
            elif role == "assistant":
                last_assistant_content = content
                self._event_bus.publish(
                    AssistantSaidEvent(agent_id=agent_id, message=content)
                )
                self._process_subagent_calls(agent_id, content)

        if metadata.model or metadata.max_tokens or metadata.input_tokens:
            self._event_bus.publish(
                AssistantRespondedEvent(
                    agent_id=agent_id,
                    response=last_assistant_content,
                    model=metadata.model,
                    max_tokens=metadata.max_tokens,
                    input_tokens=metadata.input_tokens,
                )
            )

    def _process_subagent_calls(self, parent_agent_id: AgentId, content: str) -> None:
        parsed = parse_tool_calls(content, self._tool_syntax)
        for tool_call in parsed.tool_calls:
            if tool_call.name == "subagent":
                subagent_info = self._parse_subagent_args(tool_call.arguments)
                if subagent_info:
                    agent_type, _ = subagent_info
                    subagent_name = agent_type.capitalize()
                    subagent_id = AgentId(f"{parent_agent_id.raw}/{subagent_name}")
                    subagent_metadata = self._session_storage.load_metadata(subagent_id)

                    self._event_bus.publish(
                        AgentStartedEvent(
                            agent_id=subagent_id,
                            agent_name=agent_type.capitalize(),
                            model=subagent_metadata.model,
                        )
                    )
                    self._replay_agent(subagent_id)

    def _parse_subagent_args(self, arguments: str) -> tuple[str, str] | None:
        parts = arguments.strip().split(None, 1)
        if len(parts) < 2:
            return None
        return parts[0], parts[1]

    def _extract_agent_name(self, agent_id: AgentId) -> str:
        raw = agent_id.raw
        if "/" in raw:
            return raw.rsplit("/", 1)[1]
        return raw
