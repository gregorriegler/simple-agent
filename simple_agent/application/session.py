from dataclasses import dataclass

from simple_agent.application.agent import Agent
from simple_agent.application.display_type import DisplayType
from simple_agent.application.events import SessionStartedEvent
from simple_agent.application.input import Input
from simple_agent.application.persisted_messages import PersistedMessages
from simple_agent.application.session_storage import SessionStorage
from simple_agent.application.system_prompt import SystemPrompt
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
    continue_session: bool,
    agent_id,
    system_prompt: SystemPrompt,
    user_input: Input,
    llm,
    tool_library,
    session_storage: SessionStorage,
    event_bus,
    todo_cleanup: TodoCleanup,
    agent_name: str = "Agent"
):
    if not continue_session:
        todo_cleanup.cleanup_all_todos()

    event_bus.publish(SessionStartedEvent(agent_id, continue_session))

    if continue_session:
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
        agent_id,
        agent_name,
        tool_library,
        llm,
        user_input,
        event_bus,
        session_storage,
        persisted_messages
    )

    agent.start()


def method_name(
    args, agent_library, display, event_bus, llm, prompt, session_storage, starting_agent_type, todo_cleanup, tools,
    user_input
    ):
    tools_documentation = generate_tools_documentation(tools.tools, agent_library.list_agent_types())
    system_prompt = prompt.render(tools_documentation)
    run_session(
        args.continue_session,
        starting_agent_type,
        system_prompt,
        user_input,
        llm,
        tools,
        session_storage,
        event_bus,
        todo_cleanup,
        prompt.name
    )
    display.exit()
