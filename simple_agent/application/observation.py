from .agent_definition import AgentDefinition
from .agent_id import AgentId
from .agent_task_manager import AgentTaskManager
from .agent_type import AgentType
from .change_reporter import ChangeReporter
from .event_bus import EventBus
from .input import Input
from .intent import Intents
from .observer_factory import ObserverAgentFactory, ObserverFactory
from .observer_library import ObserverLibrary
from .observers import Observers


class Observation:
    def __init__(
        self,
        event_bus: EventBus,
        observer_library: ObserverLibrary,
        change_reporter: ChangeReporter,
        agent_task_manager: AgentTaskManager,
        intents: Intents,
    ):
        self._event_bus = event_bus
        self._observer_library = observer_library
        self._change_reporter = change_reporter
        self._agent_task_manager = agent_task_manager
        self._intents = intents
        self._observers: dict[AgentId, Observers] = {}

    def watch(
        self,
        agent_id: AgentId,
        definition: AgentDefinition,
        agent_input: Input,
        agent_factory: ObserverAgentFactory,
    ) -> None:
        names = definition.observers()
        if not names:
            return
        self._observers[agent_id] = Observers(
            self._event_bus,
            agent_id,
            names,
            self._change_reporter,
            ObserverFactory(
                agent_factory,
                self._observer_library,
                self._agent_task_manager,
                agent_id,
            ),
            agent_input,
            self._intents,
        )

    def resume(self, agent_id: AgentId, agent_type: AgentType) -> bool:
        observed = agent_id.parent()
        if observed is None or observed not in self._observers:
            return False
        return self._observers[observed].resume(agent_id, agent_type)
