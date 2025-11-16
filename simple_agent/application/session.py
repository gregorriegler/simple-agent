from dataclasses import dataclass

from simple_agent.application.agent import Agent
from simple_agent.application.display_type import DisplayType
from simple_agent.application.events import SessionStartedEvent
from simple_agent.application.persisted_messages import PersistedMessages
from simple_agent.application.todo_cleanup import TodoCleanup
from simple_agent.application.tool_documentation import generate_tools_documentation


@dataclass
class SessionArgs:
    continue_session: bool
    start_message: str | None
    show_system_prompt: bool = False
    display_type: DisplayType = DisplayType.TEXTUAL
    stub_llm: bool = False
    non_interactive: bool = False


def run_session(
    args,
    agent_library,
    display,
    event_bus,
    llm,
    prompt,
    session_storage,
    starting_agent_type,
    todo_cleanup,
    tools,
    user_input
):
    tools_documentation = generate_tools_documentation(tools.tools, agent_library.list_agent_types())
    system_prompt = prompt.render(tools_documentation)

    if not args.continue_session:
        todo_cleanup.cleanup_all_todos()

    event_bus.publish(SessionStartedEvent(starting_agent_type, args.continue_session))

    if args.continue_session:
        persisted_messages = PersistedMessages(
            session_storage,
            session_storage.load().to_list(),
        )
    else:
        persisted_messages = PersistedMessages(
            session_storage,
            system_prompt=system_prompt,
        )

    agent = Agent(
        starting_agent_type,
        prompt.agent_name,
        tools,
        llm,
        user_input,
        event_bus,
        session_storage,
        persisted_messages
    )

    agent.start()
