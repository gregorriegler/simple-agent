from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_type import AgentType
from simple_agent.application.events import (
    AgentEvent,
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    ModelChangedEvent,
    SessionClearedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptedEvent,
)
from simple_agent.application.tool_library import ParsedTool, RawToolCall
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus


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
                "agent_type": event.agent_type.raw if event.agent_type else "",
            }
        elif isinstance(event, AgentFinishedEvent):
            return {
                "type": "AgentFinishedEvent",
                "agent_id": agent_id_raw,
            }
        elif isinstance(event, ToolCalledEvent):
            return {
                "type": "ToolCalledEvent",
                "agent_id": agent_id_raw,
                "call_id": event.call_id,
                "tool_name": event.tool.name if event.tool else "",
                "tool_arguments": event.tool.arguments if event.tool else "",
                "tool_body": event.tool.body if event.tool else "",
            }
        elif isinstance(event, ToolResultEvent):
            status = "success"
            if event.result:
                if event.result.cancelled:
                    status = "cancelled"
                elif not event.result.success:
                    status = "failure"

            return {
                "type": "ToolResultEvent",
                "agent_id": agent_id_raw,
                "call_id": event.call_id,
                "result_message": event.result.message if event.result else "",
                "display_title": event.result.display_title if event.result else "",
                "display_body": event.result.display_body if event.result else "",
                "display_language": event.result.display_language
                if event.result
                else "",
                "status": status,
            }
        elif isinstance(event, SessionClearedEvent):
            return {
                "type": "SessionClearedEvent",
                "agent_id": agent_id_raw,
            }
        elif isinstance(event, SessionStartedEvent):
            return {
                "type": "SessionStartedEvent",
                "agent_id": agent_id_raw,
                "is_continuation": event.is_continuation,
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
            agent_type_str = data.get("agent_type", "")
            return AgentStartedEvent(
                agent_id=agent_id,
                agent_name=data.get("agent_name", ""),
                model=data.get("model", ""),
                agent_type=AgentType(agent_type_str) if agent_type_str else None,
            )
        elif event_type == "AgentFinishedEvent":
            return AgentFinishedEvent(agent_id=agent_id)
        elif event_type == "ToolCalledEvent":
            tool_name = data.get("tool_name", "")
            tool_args = data.get("tool_arguments", "")
            tool_body = data.get("tool_body", "")
            tool = ParsedTool(RawToolCall(tool_name, tool_args, tool_body), None)
            return ToolCalledEvent(
                agent_id=agent_id,
                call_id=data.get("call_id", ""),
                tool=tool,
            )
        elif event_type == "ToolResultEvent":
            status_str = data.get("status", "success")
            try:
                status = ToolResultStatus(status_str)
            except ValueError:
                status = ToolResultStatus.SUCCESS

            return ToolResultEvent(
                agent_id=agent_id,
                call_id=data.get("call_id", ""),
                result=SingleToolResult(
                    message=data.get("result_message", ""),
                    display_title=data.get("display_title", ""),
                    display_body=data.get("display_body", ""),
                    display_language=data.get("display_language", ""),
                    status=status,
                ),
            )
        elif event_type == "SessionClearedEvent":
            return SessionClearedEvent(agent_id=agent_id)
        elif event_type == "SessionStartedEvent":
            return SessionStartedEvent(
                agent_id=agent_id,
                is_continuation=data.get("is_continuation", False),
            )
        elif event_type == "ModelChangedEvent":
            return ModelChangedEvent(
                agent_id=agent_id,
                old_model=data.get("old_model", ""),
                new_model=data.get("new_model", ""),
            )
        else:
            raise ValueError(f"Unknown event type: {event_type}")
