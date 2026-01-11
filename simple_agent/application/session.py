import asyncio
from dataclasses import dataclass

from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.display_type import DisplayType
from simple_agent.application.event_bus import EventBus
from simple_agent.application.event_store import EventStore
from simple_agent.application.events import SessionStartedEvent
from simple_agent.application.events_to_messages import events_to_messages
from simple_agent.application.history_replayer import HistoryReplayer
from simple_agent.application.llm import LLMProvider, Messages
from simple_agent.application.project_tree import ProjectTree
from simple_agent.application.todo_cleanup import TodoCleanup
from simple_agent.application.tool_library_factory import ToolLibraryFactory
from simple_agent.application.user_input import UserInput


@dataclass
class SessionArgs:
    continue_session: bool = False
    start_message: str | None = None
    show_system_prompt: bool = False
    display_type: DisplayType = DisplayType.TEXTUAL
    stub_llm: bool = False
    non_interactive: bool = False
    agent: str | None = None


class Session:
    def __init__(
        self,
        event_bus: EventBus,
        tool_library_factory: ToolLibraryFactory,
        agent_library: AgentLibrary,
        user_input: UserInput,
        todo_cleanup: TodoCleanup,
        llm_provider: LLMProvider,
        project_tree: ProjectTree,
        event_store: EventStore | None = None,
    ):
        self._event_bus = event_bus
        self._tool_library_factory = tool_library_factory
        self._agent_library = agent_library
        self._user_input = user_input
        self._todo_cleanup = todo_cleanup
        self._llm_provider = llm_provider
        self._project_tree = project_tree
        self._event_store = event_store

    async def run_async(
        self,
        args: SessionArgs,
        starting_agent_id: AgentId,
    ):
        agent_factory = AgentFactory(
            self._event_bus,
            self._tool_library_factory,
            self._agent_library,
            self._user_input,
            self._llm_provider,
            self._project_tree,
            event_store=self._event_store,
        )

        self._event_bus.publish(
            SessionStartedEvent(starting_agent_id, args.continue_session)
        )

        unfinished_subagents = []
        if args.continue_session and self._event_store:
            history_replayer = HistoryReplayer(self._event_bus, self._event_store)
            unfinished_subagents = history_replayer.replay_all_agents(starting_agent_id)
            events = self._event_store.load_events(starting_agent_id)
            context = events_to_messages(events, starting_agent_id)
        else:
            context = Messages()

        agent_definition = self._agent_library._starting_agent_definition()
        agent = agent_factory.create_agent(
            starting_agent_id,
            agent_definition,
            args.start_message,
            context,
            agent_definition.agent_type,
        )

        for event in unfinished_subagents:
            subagent = agent_factory.create_agent_from_history(
                event.agent_id, event.agent_type
            )
            asyncio.create_task(subagent.start())

        await agent.start()
