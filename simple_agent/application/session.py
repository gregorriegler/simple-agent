import asyncio
from collections.abc import Callable
from dataclasses import dataclass

from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.agent_task_manager import AgentTaskManager
from simple_agent.application.change_reporter import ChangeReporter
from simple_agent.application.checkpoint_detector import CheckpointDetector
from simple_agent.application.display_type import DisplayType
from simple_agent.application.event_bus import EventBus
from simple_agent.application.event_store import EventStore
from simple_agent.application.events import SessionStartedEvent
from simple_agent.application.events_to_messages import events_to_messages
from simple_agent.application.history_replayer import HistoryReplayer
from simple_agent.application.input import Input
from simple_agent.application.llm import LLMProvider, Messages
from simple_agent.application.observer_factory import ObserverFactory
from simple_agent.application.observer_library import ObserverLibrary
from simple_agent.application.observers import Observers
from simple_agent.application.project_tree import ProjectTree
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
        starting_agent_id: AgentId,
        event_bus: EventBus,
        tool_library_factory: ToolLibraryFactory,
        agent_library: AgentLibrary,
        user_input: UserInput,
        llm_provider: LLMProvider,
        project_tree: ProjectTree,
        event_store: EventStore,
        agent_task_manager: AgentTaskManager,
        on_replay_complete: Callable[[], None] | None = None,
        observer_library: ObserverLibrary | None = None,
        change_reporter: ChangeReporter | None = None,
    ):
        self._starting_agent_id = starting_agent_id
        self._event_bus = event_bus
        self._tool_library_factory = tool_library_factory
        self._agent_library = agent_library
        self._user_input = user_input
        self._llm_provider = llm_provider
        self._project_tree = project_tree
        self._event_store = event_store
        self._agent_task_manager = agent_task_manager
        self._on_replay_complete = on_replay_complete
        self._observer_library = observer_library
        self._change_reporter = change_reporter
        self._checkpoint_detector = CheckpointDetector(event_bus)

    def _observe(
        self, agent_factory: AgentFactory, agent_definition, agent_input: Input
    ) -> None:
        if not self._observer_library or not self._change_reporter:
            return
        names = agent_definition.observers()
        if not names:
            return
        Observers(
            self._event_bus,
            self._starting_agent_id,
            names,
            self._change_reporter,
            ObserverFactory(
                agent_factory,
                self._observer_library,
                self._agent_task_manager,
                self._starting_agent_id,
            ),
            agent_input,
        )

    async def run_async(
        self,
        args: SessionArgs,
    ):
        agent_factory = AgentFactory(
            self._event_bus,
            self._tool_library_factory,
            self._agent_library,
            self._user_input,
            self._llm_provider,
            self._project_tree,
            event_store=self._event_store,
            agent_task_manager=self._agent_task_manager,
        )

        self._event_bus.publish(
            SessionStartedEvent(self._starting_agent_id, args.continue_session)
        )

        unfinished_subagents = []
        if args.continue_session:
            history_replayer = HistoryReplayer(self._event_bus, self._event_store)
            unfinished_subagents = await history_replayer.replay_all_agents_async(
                self._starting_agent_id
            )
            events = self._event_store.load_events(self._starting_agent_id)
            context = events_to_messages(events, self._starting_agent_id)
        else:
            context = Messages()

        if self._on_replay_complete:
            self._on_replay_complete()

        agent_definition = self._agent_library._starting_agent_definition()
        agent_input = agent_factory.create_input(args.start_message)
        agent = agent_factory.create_agent(
            self._starting_agent_id,
            agent_definition,
            None,
            context,
            agent_definition.agent_type,
            user_input=agent_input,
        )

        self._observe(agent_factory, agent_definition, agent_input)

        for event in unfinished_subagents:
            subagent = agent_factory.create_agent_from_history(
                event.agent_id, event.agent_type
            )
            asyncio.create_task(subagent.start())

        await agent.start()
