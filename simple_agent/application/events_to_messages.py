from collections.abc import Sequence

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentEvent,
    AssistantRespondedEvent,
    SessionClearedEvent,
    ToolResultEvent,
    UserPromptedEvent,
)
from simple_agent.application.llm import Messages


def events_to_messages(events: Sequence[AgentEvent], agent_id: AgentId) -> Messages:
    messages = Messages()

    for event in events:
        if event.agent_id != agent_id:
            continue

        if isinstance(event, UserPromptedEvent):
            messages.user_says(event.input_text)
        elif isinstance(event, AssistantRespondedEvent):
            messages.assistant_says(event.response)
        elif isinstance(event, ToolResultEvent):
            if event.result is not None:
                messages.user_says(event.result.message)
        elif isinstance(event, SessionClearedEvent):
            messages.clear()

    return messages
