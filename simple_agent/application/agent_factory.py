import asyncio

from simple_agent.application.agent import Agent
from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId, AgentIdSuffixer
from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.agent_task_manager import AgentTaskManager
from simple_agent.application.agent_type import AgentType
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.brain import Brain
from simple_agent.application.event_bus import EventBus
from simple_agent.application.event_store import EventStore
from simple_agent.application.events_to_messages import (
    events_to_messages,
)
from simple_agent.application.inbox import Inbox
from simple_agent.application.inboxes import Inboxes
from simple_agent.application.llm import LLMProvider, Messages
from simple_agent.application.observation import Observation
from simple_agent.application.on_complete import OnComplete
from simple_agent.application.project_tree import ProjectTree
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library_factory import (
    ToolContext,
    ToolLibraryFactory,
)
from simple_agent.application.tool_results import SingleToolResult


class AgentFactory:
    def __init__(
        self,
        event_bus: EventBus,
        tool_library_factory: ToolLibraryFactory,
        agent_library: AgentLibrary,
        inboxes: Inboxes,
        llm_provider: LLMProvider,
        project_tree: ProjectTree,
        event_store: EventStore,
        agent_task_manager: AgentTaskManager,
        observation: Observation | None = None,
    ):
        self._event_bus = event_bus
        self._tool_library_factory = tool_library_factory
        self._agent_library = agent_library
        self._inboxes = inboxes
        self._agent_suffixer = AgentIdSuffixer()
        self._llm_provider = llm_provider
        self._project_tree = project_tree
        self._event_store = event_store
        self._agent_task_manager = agent_task_manager
        self._observation = observation

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    def create_inbox(
        self, agent_id: AgentId, initial_message: str | None = None
    ) -> Inbox:
        inbox = self._inboxes.for_agent(agent_id)
        if initial_message:
            inbox.put(initial_message)
        return inbox

    def create_spawner(
        self, parent_agent_id: AgentId, parent_inbox: Inbox
    ) -> SubagentSpawner:
        async def spawn(agent_type, task_description, background=False):
            definition = self._agent_library.read_agent_definition(agent_type)
            agent_id = parent_agent_id.create_subagent_id(
                definition.agent_name(), self._agent_suffixer
            )
            context = self.history_of(agent_id)
            inbox = self.create_inbox(agent_id, task_description)

            subagent = self.create_agent(
                agent_id,
                definition,
                None,
                context,
                agent_type,
                inbox=inbox,
                on_complete=OnComplete.CLOSE if background else OnComplete.HUMAN_REVIEW,
            )
            task = self._agent_task_manager.start_task(agent_id, subagent.start())
            if background:
                task.add_done_callback(
                    lambda done: self._report_completion(parent_inbox, agent_id, done)
                )
                return SingleToolResult("Subagent started")
            try:
                return await asyncio.shield(task)
            except asyncio.CancelledError:
                await self._end(task, inbox)
                raise

        return spawn

    @staticmethod
    async def _end(task: asyncio.Task, inbox: Inbox) -> None:
        """The parent was interrupted: its subagent stops and is not asked for more."""
        inbox.close()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    @staticmethod
    def _report_completion(
        parent_inbox: Inbox, agent_id: AgentId, done: asyncio.Task
    ) -> None:
        if done.cancelled() or done.exception() is not None:
            return
        result = done.result()
        outcome = "completed" if result.success else "failed"
        parent_inbox.put(f"Subagent {agent_id} {outcome}: {result}")

    def history_of(self, agent_id: AgentId) -> Messages:
        events = self._event_store.load_events(agent_id)
        return events_to_messages(events, agent_id)

    def create_agent_from_history(
        self, agent_id: AgentId, agent_type: AgentType
    ) -> Agent:
        definition = self._agent_library.read_agent_definition(agent_type)
        context = self.history_of(agent_id)

        return self.create_agent(agent_id, definition, None, context, agent_type)

    def create_agent(
        self,
        agent_id: AgentId,
        definition: AgentDefinition,
        initial_message: str | None,
        messages: Messages,
        agent_type: AgentType | None = None,
        inbox: Inbox | None = None,
        on_complete: OnComplete = OnComplete.HUMAN_REVIEW,
    ) -> Agent:
        inbox = inbox or self.create_inbox(agent_id, initial_message)
        brain = self._build_brain(agent_id, definition, inbox)
        messages.seed_system_prompt(brain.system_prompt)
        if self._observation:
            self._observation.watch(agent_id, definition, inbox, self)

        return Agent(
            agent_id=agent_id,
            brain=brain,
            llm_provider=self._llm_provider,
            inbox=inbox,
            event_bus=self._event_bus,
            context=messages,
            agent_type=agent_type,
            available_agents=self._agent_library.list_agent_types(),
            brain_factory=self,
            on_complete=on_complete,
        )

    def build_brain(
        self, agent_id: AgentId, agent_type: AgentType, inbox: Inbox
    ) -> Brain:
        definition = self._agent_library.read_agent_definition(agent_type)
        return self._build_brain(agent_id, definition, inbox)

    def _build_brain(
        self, agent_id: AgentId, definition: AgentDefinition, inbox: Inbox
    ) -> Brain:
        tool_context = ToolContext(definition.tool_keys(), agent_id, inbox)
        spawner = self.create_spawner(agent_id, inbox)
        tools = self._tool_library_factory.create(
            tool_context, spawner, AgentTypes(self._agent_library.list_agent_types())
        )
        system_prompt = definition.prompt().render(self._project_tree)
        return Brain(
            name=definition.agent_name(),
            system_prompt=system_prompt,
            llm=self._llm_provider.get(definition.model(), tools=tools.tools),
            tools=tools,
        )
