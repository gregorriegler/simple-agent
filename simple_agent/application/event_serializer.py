from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentEvent,
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    ModelChangedEvent,
    SessionClearedEvent,
    ToolResultEvent,
    UserPromptedEvent,
)
from simple_agent.application.tool_results import SingleToolResult


class EventSerializer:
    @staticmethod
    def to_dict(event: AgentEvent) -> dict:
        agent_id_raw = event.agent_id.raw if event.agent_id else None

        if isinstance(event, UserPromptedEvent):
            return {
                "type": "UserPromptedEvent",
                "agent_id": agent_id_raw,
                "input_text": event.input_text,
            }
        elif isinstance(event, AssistantRespondedEvent):
            return {
                "type": "AssistantRespondedEvent",
                "agent_id": agent_id_raw,
                "response": event.response,
                "model": event.model,
                "token_usage_display": event.token_usage_display,
            }
        elif isinstance(event, AgentStartedEvent):
            return {
                "type": "AgentStartedEvent",
                "agent_id": agent_id_raw,
                "agent_name": event.agent_name,
                "model": event.model,
                "agent_type": event.agent_type,
            }
        elif isinstance(event, AgentFinishedEvent):
            return {
                "type": "AgentFinishedEvent",
                "agent_id": agent_id_raw,
            }
        elif isinstance(event, ToolResultEvent):
            return {
                "type": "ToolResultEvent",
                "agent_id": agent_id_raw,
                "call_id": event.call_id,
                "result_message": event.result.message if event.result else "",
            }
        elif isinstance(event, SessionClearedEvent):
            return {
                "type": "SessionClearedEvent",
                "agent_id": agent_id_raw,
            }
        elif isinstance(event, ModelChangedEvent):
            return {
                "type": "ModelChangedEvent",
                "agent_id": agent_id_raw,
                "old_model": event.old_model,
                "new_model": event.new_model,
            }
        else:
            raise ValueError(f"Unknown event type: {type(event).__name__}")

    @staticmethod
    def from_dict(data: dict) -> AgentEvent:
        event_type = data.get("type")
        agent_id = AgentId(data["agent_id"]) if data.get("agent_id") else None

        if event_type == "UserPromptedEvent":
            return UserPromptedEvent(
                agent_id=agent_id,
                input_text=data.get("input_text", ""),
            )
        elif event_type == "AssistantRespondedEvent":
            return AssistantRespondedEvent(
                agent_id=agent_id,
                response=data.get("response", ""),
                model=data.get("model", ""),
                token_usage_display=data.get("token_usage_display", ""),
            )
        elif event_type == "AgentStartedEvent":
            return AgentStartedEvent(
                agent_id=agent_id,
                agent_name=data.get("agent_name", ""),
                model=data.get("model", ""),
                agent_type=data.get("agent_type", ""),
            )
        elif event_type == "AgentFinishedEvent":
            return AgentFinishedEvent(agent_id=agent_id)
        elif event_type == "ToolResultEvent":
            return ToolResultEvent(
                agent_id=agent_id,
                call_id=data.get("call_id", ""),
                result=SingleToolResult(message=data.get("result_message", "")),
            )
        elif event_type == "SessionClearedEvent":
            return SessionClearedEvent(agent_id=agent_id)
        elif event_type == "ModelChangedEvent":
            return ModelChangedEvent(
                agent_id=agent_id,
                old_model=data.get("old_model", ""),
                new_model=data.get("new_model", ""),
            )
        else:
            raise ValueError(f"Unknown event type: {event_type}")
