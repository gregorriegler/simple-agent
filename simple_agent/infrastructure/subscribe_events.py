from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AgentStartedEvent,
    AgentFinishedEvent,
    AssistantSaidEvent,
    AssistantRespondedEvent,
    ErrorEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.infrastructure.event_logger import EventLogger
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from simple_agent.infrastructure.textual.textual_display import TextualDisplay


def subscribe_events(
    event_bus: SimpleEventBus,
    event_logger: EventLogger,
    todo_cleanup: FileSystemTodoCleanup,
    display: TextualDisplay,
):
    event_bus.subscribe(SessionStartedEvent, event_logger.log_event)
    event_bus.subscribe(UserPromptRequestedEvent, event_logger.log_event)
    event_bus.subscribe(UserPromptedEvent, event_logger.log_event)
    event_bus.subscribe(AssistantSaidEvent, event_logger.log_event)
    event_bus.subscribe(ToolCalledEvent, event_logger.log_event)
    event_bus.subscribe(ToolResultEvent, event_logger.log_event)
    event_bus.subscribe(SessionInterruptedEvent, event_logger.log_event)
    event_bus.subscribe(ErrorEvent, event_logger.log_event)
    event_bus.subscribe(SessionEndedEvent, event_logger.log_event)
    event_bus.subscribe(AgentStartedEvent, event_logger.log_event)
    event_bus.subscribe(
        AgentFinishedEvent,
        lambda event: todo_cleanup.cleanup_todos_for_agent(event.agent_id) if event.agent_id.has_parent() else None,
    )
    event_bus.subscribe(SessionStartedEvent, display.start_session)
    event_bus.subscribe(UserPromptRequestedEvent, display.wait_for_input)
    event_bus.subscribe(AssistantRespondedEvent, display.assistant_responded)
    event_bus.subscribe(UserPromptedEvent, display.user_says)
    event_bus.subscribe(AssistantSaidEvent, display.assistant_says)
    event_bus.subscribe(ToolCalledEvent, display.tool_call)
    event_bus.subscribe(ToolResultEvent, display.tool_result)
    event_bus.subscribe(SessionInterruptedEvent, display.interrupted)
    event_bus.subscribe(ErrorEvent, display.error_occurred)
    event_bus.subscribe(SessionEndedEvent, display.exit)
    event_bus.subscribe(AgentStartedEvent, display.agent_created)