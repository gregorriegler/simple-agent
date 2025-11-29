from dataclasses import dataclass
from typing import Callable, Any

from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.app_context import AppContext
from simple_agent.application.display_type import DisplayType
from simple_agent.application.events import SessionStartedEvent
from simple_agent.application.persisted_messages import PersistedMessages


@dataclass
class SessionArgs:
    continue_session: bool = False
    start_message: str | None = None
    show_system_prompt: bool = False
    display_type: DisplayType = DisplayType.TEXTUAL
    stub_llm: bool = False
    non_interactive: bool = False
    agent: str | None = None
    test_mode: bool = False
    on_user_prompt_requested: Callable[[Any], None] | None = None



def run_session(
    args: SessionArgs,
    app_context: AppContext,
    starting_agent_id: AgentId,
    todo_cleanup,
    user_input,
    agent_definition: AgentDefinition
):
    if not args.continue_session:
        todo_cleanup.cleanup_all_todos()

    app_context.event_bus.publish(SessionStartedEvent(starting_agent_id, args.continue_session))

    if args.continue_session:
        persisted_messages = PersistedMessages(
            app_context.session_storage,
            app_context.session_storage.load().to_list(),
        )
    else:
        persisted_messages = PersistedMessages(app_context.session_storage)

    agent = app_context.agent_factory.create_root_agent(
        starting_agent_id,
        agent_definition,
        user_input,
        persisted_messages
    )

    agent.start()
