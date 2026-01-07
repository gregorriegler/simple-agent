from dataclasses import dataclass
from typing import Any, ClassVar

from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.tool_results import ToolResult


@dataclass
class AgentEvent:
    agent_id: AgentId | None = None
    event_name: ClassVar[str] = "agent_event"


@dataclass
class AssistantSaidEvent(AgentEvent):
    event_name: ClassVar[str] = "assistant_said"
    message: str = ""


@dataclass
class ToolCalledEvent(AgentEvent):
    event_name: ClassVar[str] = "tool_called"
    call_id: str = ""
    tool: Any = None


@dataclass
class ToolResultEvent(AgentEvent):
    event_name: ClassVar[str] = "tool_result"
    call_id: str = ""
    result: ToolResult | None = None


@dataclass
class ToolCancelledEvent(AgentEvent):
    event_name: ClassVar[str] = "tool_cancelled"
    call_id: str = ""


@dataclass
class SessionStartedEvent(AgentEvent):
    event_name: ClassVar[str] = "session_started"
    is_continuation: bool = False


@dataclass
class SessionInterruptedEvent(AgentEvent):
    event_name: ClassVar[str] = "session_interrupted"


@dataclass
class SessionClearedEvent(AgentEvent):
    event_name: ClassVar[str] = "session_cleared"


@dataclass
class SessionEndedEvent(AgentEvent):
    event_name: ClassVar[str] = "session_ended"


@dataclass
class UserPromptRequestedEvent(AgentEvent):
    event_name: ClassVar[str] = "user_prompt_requested"


@dataclass
class UserPromptedEvent(AgentEvent):
    event_name: ClassVar[str] = "user_prompted"
    input_text: str = ""


@dataclass
class AssistantRespondedEvent(AgentEvent):
    event_name: ClassVar[str] = "assistant_responded"
    response: str = ""
    model: str = ""
    max_tokens: int = 0
    input_tokens: int = 0


@dataclass
class AgentFinishedEvent(AgentEvent):
    event_name: ClassVar[str] = "agent_finished"


@dataclass
class AgentStartedEvent(AgentEvent):
    event_name: ClassVar[str] = "agent_started"
    agent_name: str = ""
    model: str = ""


@dataclass
class ErrorEvent(AgentEvent):
    event_name: ClassVar[str] = "error"
    message: str = ""


@dataclass
class ModelChangedEvent(AgentEvent):
    event_name: ClassVar[str] = "model_changed"
    old_model: str = ""
    new_model: str = ""


@dataclass
class AgentChangedEvent(AgentEvent):
    event_name: ClassVar[str] = "agent_changed"
    agent_definition: AgentDefinition | None = None
