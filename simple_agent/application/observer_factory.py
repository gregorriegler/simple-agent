from .agent_factory import AgentFactory
from .agent_id import AgentId, AgentIdSuffixer
from .agent_task_manager import AgentTaskManager
from .agent_type import AgentType
from .input import Input
from .llm import Messages
from .observer_definition import ObserverDefinition
from .observer_input import ObserverInput
from .observer_library import ObserverLibrary


class SpawnedObserver:
    def __init__(self, agent_id: AgentId, observer_input: ObserverInput):
        self.agent_id = agent_id
        self._input = observer_input

    def observe(self, packet: str) -> None:
        self._input.submit(packet)

    def close(self) -> None:
        self._input.close()


class ObserverFactory:
    def __init__(
        self,
        agent_factory: AgentFactory,
        observer_library: ObserverLibrary,
        agent_task_manager: AgentTaskManager,
        observed_agent_id: AgentId,
    ):
        self._agent_factory = agent_factory
        self._observer_library = observer_library
        self._agent_task_manager = agent_task_manager
        self._observed_agent_id = observed_agent_id
        self._suffixer = AgentIdSuffixer()

    def __call__(self, name: str) -> SpawnedObserver:
        definition = self._observer_library.read_observer_definition(name)
        observer_id = self._claim_observer_id(definition.agent_name())
        return self._start(observer_id, definition, Messages(), AgentType(name))

    def create_from_history(
        self, agent_id: AgentId, agent_type: AgentType
    ) -> SpawnedObserver:
        definition = self._observer_library.read_observer_definition(agent_type.raw)
        self._claim_observer_id(definition.agent_name())
        context = self._agent_factory.history_of(agent_id)
        return self._start(agent_id, definition, context, agent_type)

    def _claim_observer_id(self, agent_name: str) -> AgentId:
        return self._observed_agent_id.create_subagent_id(agent_name, self._suffixer)

    def _start(
        self,
        observer_id: AgentId,
        definition: ObserverDefinition,
        context: Messages,
        agent_type: AgentType,
    ) -> SpawnedObserver:
        observer_input = ObserverInput()
        observer = self._agent_factory.create_agent(
            observer_id,
            definition,
            None,
            context,
            agent_type,
            user_input=Input(observer_input),
        )
        self._agent_task_manager.start_task(observer_id, observer.start())
        return SpawnedObserver(observer_id, observer_input)
