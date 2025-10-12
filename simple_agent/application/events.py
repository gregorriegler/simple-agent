from dataclasses import dataclass
from enum import Enum


@dataclass
class AgentEvent:
    agent_id: str


@dataclass
class AssistantSaidEvent(AgentEvent):
    message: str


@dataclass
class ToolCalledEvent(AgentEvent):
    tool: any


@dataclass
class ToolResultEvent(AgentEvent):
    result: str


@dataclass
class SessionStartedEvent(AgentEvent):
    is_continuation: bool


@dataclass
class SessionInterruptedEvent(AgentEvent):
    pass


@dataclass
class SessionEndedEvent(AgentEvent):
    pass


@dataclass
class UserPromptRequestedEvent(AgentEvent):
    pass


@dataclass
class UserPromptedEvent(AgentEvent):
    input_text: str


class EventType(str, Enum):
    TOOL_CALLED = "tool_called"
    ASSISTANT_SAID = "assistant_said"
    TOOL_RESULT = "tool_result"
    SESSION_STARTED = "session_started"
    SESSION_INTERRUPTED = "session_interrupted"
    SESSION_ENDED = "session_ended"
    USER_PROMPT_REQUESTED = "user_prompt_requested"
    USER_PROMPTED = "user_prompted"
