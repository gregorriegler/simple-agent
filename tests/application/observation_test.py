from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_task_manager import AgentTaskManager
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import AgentFinishedEvent
from simple_agent.application.inbox import Inbox
from simple_agent.application.inboxes import AgentInboxes
from simple_agent.application.llm import Messages
from simple_agent.application.observation import Observation
from tests.application.observers_test import ChangeReporterStub, IntentsStub
from tests.session_test_bed import ObserverLibraryStub
from tests.system_prompt_generator_test import GroundRulesStub

AGENT = AgentId("Agent")


class AgentStub:
    async def start(self):
        pass


class ObserverAgentFactoryStub:
    def __init__(self):
        self.created = []

    def create_agent(
        self, agent_id, definition, initial_message, messages, *args, **kwargs
    ):
        self.created.append(agent_id)
        return AgentStub()

    def history_of(self, agent_id):
        return Messages()


def observed_by(observers: list[str]) -> AgentDefinition:
    return AgentDefinition(
        AgentType("agent"),
        f"---\nname: Agent\nobservers: {observers}\n---",
        GroundRulesStub("Test system prompt"),
    )


async def test_a_finished_agents_observers_cannot_be_resumed():
    event_bus = SimpleEventBus()
    factory = ObserverAgentFactoryStub()
    observation = Observation(
        event_bus,
        ObserverLibraryStub(),
        ChangeReporterStub(),
        AgentTaskManager(),
        IntentsStub(),
        AgentInboxes(),
    )
    observation.watch(AGENT, observed_by(["naming"]), Inbox(), factory)

    event_bus.publish(AgentFinishedEvent(AGENT))
    resumed = observation.resume(AgentId("Agent/Naming"), AgentType("naming"))

    assert not resumed
    assert factory.created == []
