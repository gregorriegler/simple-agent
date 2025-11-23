from dataclasses import dataclass

from simple_agent.application.agent import Agent
from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_factory import ToolContext
from simple_agent.application.agent_id import AgentId
from simple_agent.application.app_context import AppContext
from simple_agent.application.display_type import DisplayType
from simple_agent.application.events import SessionStartedEvent
from simple_agent.application.persisted_messages import PersistedMessages
from simple_agent.application.tool_documentation import generate_tools_documentation


@dataclass
class SessionArgs:
    continue_session: bool = False
    start_message: str | None = None
    show_system_prompt: bool = False
    display_type: DisplayType = DisplayType.TEXTUAL
    stub_llm: bool = False
    non_interactive: bool = False
    agent: str | None = None



def run_session(
    args: SessionArgs,
    app_context: AppContext,
    starting_agent_id: AgentId,
    todo_cleanup,
    user_input,
    agent_definition: AgentDefinition
):
    tool_context = ToolContext(
        agent_definition.tool_keys(),
        starting_agent_id,
        lambda agent_type, task_description: app_context.agent_factory.spawn_subagent(
            starting_agent_id, agent_type, task_description, 0
        )
    )
    tools = app_context.tool_library_factory.create(tool_context)
    tools_documentation = generate_tools_documentation(tools.tools, app_context.agent_library.list_agent_types())
    system_prompt = agent_definition.prompt().render(tools_documentation)

    if not args.continue_session:
        todo_cleanup.cleanup_all_todos()

    app_context.event_bus.publish(SessionStartedEvent(starting_agent_id, args.continue_session))

    if args.continue_session:
        persisted_messages = PersistedMessages(
            app_context.session_storage,
            app_context.session_storage.load().to_list(),
        )
    else:
        persisted_messages = PersistedMessages(
            app_context.session_storage,
            system_prompt=system_prompt,
        )

    agent = Agent(
        starting_agent_id,
        agent_definition.agent_name(),
        tools,
        app_context.llm,
        user_input,
        app_context.event_bus,
        app_context.session_storage,
        persisted_messages
    )

    agent.start()
