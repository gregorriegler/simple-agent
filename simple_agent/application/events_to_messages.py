from collections.abc import Sequence

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentEvent,
    AssistantRespondedEvent,
    SessionClearedEvent,
    ToolCalledEvent,
    ToolCancelledEvent,
    ToolResultEvent,
    UserPromptedEvent,
)
from simple_agent.application.llm import Messages
from simple_agent.application.tool_library import RawToolCall
from simple_agent.application.tools_executor import INTERRUPTED_RESULT


class _AssistantTurn:
    """Collects an assistant response and the tool calls that followed it."""

    def __init__(self) -> None:
        self.answer = ""
        self.calls: list[RawToolCall] = []

    def flush(self, messages: Messages) -> None:
        messages.assistant_says(self.answer, self.calls)
        self.answer = ""
        self.calls = []


def events_to_messages(events: Sequence[AgentEvent], agent_id: AgentId) -> Messages:
    messages = Messages()
    turn = _AssistantTurn()
    calls_by_id: dict[str, RawToolCall] = {}

    for event in events:
        if event.agent_id != agent_id:
            continue

        if isinstance(event, ToolCalledEvent):
            if event.call is not None:
                turn.calls.append(event.call)
                calls_by_id[event.call_id] = event.call
            continue

        turn.flush(messages)
        if isinstance(event, ToolResultEvent):
            if event.result is None:
                continue
            call = calls_by_id.pop(event.call_id, None)
            if call is not None:
                messages.tool_result(call, event.result.message)
            else:
                messages.user_says(event.result.message)
            continue
        if isinstance(event, ToolCancelledEvent):
            continue

        _interrupt_unanswered(messages, calls_by_id)
        if isinstance(event, UserPromptedEvent):
            messages.user_says(event.input_text)
        elif isinstance(event, AssistantRespondedEvent):
            turn.answer = event.response
        elif isinstance(event, SessionClearedEvent):
            messages.clear()

    turn.flush(messages)
    _interrupt_unanswered(messages, calls_by_id)
    return messages


def _interrupt_unanswered(messages: Messages, calls_by_id: dict[str, RawToolCall]):
    for call in calls_by_id.values():
        messages.tool_result(call, INTERRUPTED_RESULT)
    calls_by_id.clear()
