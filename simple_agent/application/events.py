from dataclasses import dataclass
from typing import Any, ClassVar

from simple_agent.application.agent_id import AgentId
from simple_agent.application.tool_library import ToolResult


@dataclass
class AgentEvent:
    agent_id: AgentId
    event_name: ClassVar[str] = "agent_event"


@dataclass
class AssistantSaidEvent(AgentEvent):
    event_name: ClassVar[str] = "assistant_said"
    message: str


@dataclass
class ToolCalledEvent(AgentEvent):
    event_name: ClassVar[str] = "tool_called"
    call_id: str
    tool: Any


@dataclass
class ToolResultEvent(AgentEvent):
    event_name: ClassVar[str] = "tool_result"
    call_id: str
    result: ToolResult


@dataclass
class ToolCancelledEvent(AgentEvent):
    event_name: ClassVar[str] = "tool_cancelled"
    call_id: str


@dataclass
class SessionStartedEvent(AgentEvent):
    event_name: ClassVar[str] = "session_started"
    is_continuation: bool


@dataclass
class SessionInterruptedEvent(AgentEvent):
    event_name: ClassVar[str] = "session_interrupted"


@dataclass
class SessionEndedEvent(AgentEvent):
    event_name: ClassVar[str] = "session_ended"


@dataclass
class UserPromptRequestedEvent(AgentEvent):
    event_name: ClassVar[str] = "user_prompt_requested"


@dataclass
class UserPromptedEvent(AgentEvent):
    event_name: ClassVar[str] = "user_prompted"
    input_text: str


@dataclass
class AssistantRespondedEvent(AgentEvent):
    event_name: ClassVar[str] = "assistant_responded"
    response: str
    model: str = ""
    token_count: int = 0
    max_tokens: int = 0


@dataclass
class AgentFinishedEvent(AgentEvent):
    event_name: ClassVar[str] = "agent_finished"


@dataclass
class AgentStartedEvent(AgentEvent):
    event_name: ClassVar[str] = "agent_started"
    agent_name: str
    model: str = ""


@dataclass
class ErrorEvent(AgentEvent):
    event_name: ClassVar[str] = "error"
    message: str
