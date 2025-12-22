from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AgentStartedEvent,
    AgentFinishedEvent,
    AssistantSaidEvent,
    AssistantRespondedEvent,
    ErrorEvent,
    SessionClearedEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolCancelledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.infrastructure.event_logger import EventLogger
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage


def subscribe_events(
    event_bus: SimpleEventBus,
    event_logger: EventLogger,
    todo_cleanup: FileSystemTodoCleanup,
    app: TextualApp | None = None,
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
    event_bus.subscribe(
        SessionClearedEvent,
        lambda event: todo_cleanup.cleanup_todos_for_agent(event.agent_id),
    )
    if app:
        def _post_domain_event(event):
            app.post_message(DomainEventMessage(event))
        event_bus.subscribe(AgentStartedEvent, _post_domain_event)
        event_bus.subscribe(SessionStartedEvent, _post_domain_event)
        event_bus.subscribe(UserPromptRequestedEvent, _post_domain_event)
        event_bus.subscribe(SessionClearedEvent, _post_domain_event)
        event_bus.subscribe(UserPromptedEvent, _post_domain_event)
        event_bus.subscribe(AssistantSaidEvent, _post_domain_event)
        event_bus.subscribe(AssistantRespondedEvent, _post_domain_event)
        event_bus.subscribe(ToolCalledEvent, _post_domain_event)
        event_bus.subscribe(ToolResultEvent, _post_domain_event)
        event_bus.subscribe(ToolCancelledEvent, _post_domain_event)
        event_bus.subscribe(SessionInterruptedEvent, _post_domain_event)
        event_bus.subscribe(ErrorEvent, _post_domain_event)
        event_bus.subscribe(SessionEndedEvent, _post_domain_event)
