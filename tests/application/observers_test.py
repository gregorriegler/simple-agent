from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AgentFinishedEvent,
    CheckpointReachedEvent,
    SessionClearedEvent,
    ToolCalledEvent,
)
from simple_agent.application.input import Input
from simple_agent.application.observers import Observers
from simple_agent.application.tool_library import RawToolCall
from simple_agent.application.user_input import DummyUserInput

AGENT = AgentId("Agent")
DIFF = "diff --git a/greeting.txt b/greeting.txt"


class ChangeReporterStub:
    def __init__(self, *diffs):
        self._diffs = list(diffs)

    def diff(self) -> str:
        return self._diffs.pop(0) if self._diffs else ""


class ObserverStub:
    def __init__(self, name):
        self.name = name
        self.agent_id = AgentId(f"Agent/{name}")
        self.observed = []
        self.closed = False

    def observe(self, packet: str) -> None:
        self.observed.append(packet)

    def close(self) -> None:
        self.closed = True


class ObserverFactoryStub:
    def __init__(self):
        self.created = []

    def __call__(self, name: str) -> ObserverStub:
        observer = ObserverStub(name)
        self.created.append(observer)
        return observer


class IntentStub:
    def __init__(self, intent=""):
        self._intent = intent

    def read(self) -> str:
        return self._intent


def observers_of(
    event_bus, names, change_reporter, factory, agent_input=None, intent=None
):
    return Observers(
        event_bus,
        AGENT,
        names,
        change_reporter,
        factory,
        agent_input or Input(DummyUserInput()),
        intent or IntentStub(),
    )


def test_every_observer_of_the_agent_sees_the_diff():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    observers_of(event_bus, ["naming", "errors"], ChangeReporterStub(DIFF), factory)

    event_bus.publish(CheckpointReachedEvent(AGENT))

    assert [observer.name for observer in factory.created] == ["naming", "errors"]
    assert all(observer.observed == [DIFF] for observer in factory.created)


def test_observers_stay_with_the_agent_and_are_fed_again():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    reporter = ChangeReporterStub(DIFF, "a later diff")
    observers_of(event_bus, ["naming"], reporter, factory)

    event_bus.publish(CheckpointReachedEvent(AGENT))
    event_bus.publish(CheckpointReachedEvent(AGENT))

    assert len(factory.created) == 1
    assert factory.created[0].observed == [DIFF, "a later diff"]


def test_nothing_to_observe_without_changes():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    observers_of(event_bus, ["naming"], ChangeReporterStub(""), factory)

    event_bus.publish(CheckpointReachedEvent(AGENT))

    assert factory.created == []


def test_another_agents_checkpoint_is_not_observed():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    observers_of(event_bus, ["naming"], ChangeReporterStub(DIFF), factory)

    event_bus.publish(CheckpointReachedEvent(AgentId("Other")))

    assert factory.created == []


def test_observers_are_closed_when_the_agent_finishes():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    observers_of(event_bus, ["naming"], ChangeReporterStub(DIFF), factory)

    event_bus.publish(CheckpointReachedEvent(AGENT))
    event_bus.publish(AgentFinishedEvent(AGENT))

    assert factory.created[0].closed


def test_observers_are_closed_when_the_session_is_cleared():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    observers_of(event_bus, ["naming"], ChangeReporterStub(DIFF), factory)

    event_bus.publish(CheckpointReachedEvent(AGENT))
    event_bus.publish(SessionClearedEvent(AGENT))

    assert factory.created[0].closed


def test_observers_are_recreated_after_the_session_is_cleared():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    reporter = ChangeReporterStub(DIFF, "a later diff")
    observers_of(event_bus, ["naming"], reporter, factory)

    event_bus.publish(CheckpointReachedEvent(AGENT))
    event_bus.publish(SessionClearedEvent(AGENT))
    event_bus.publish(CheckpointReachedEvent(AGENT))

    assert len(factory.created) == 2
    assert factory.created[0].closed
    assert not factory.created[1].closed


def suggest(text):
    return RawToolCall("suggest", "", body=text)


def test_what_an_observer_found_reaches_the_agent():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    agent_input = Input(DummyUserInput())
    observers_of(event_bus, ["naming"], ChangeReporterStub(DIFF), factory, agent_input)

    event_bus.publish(CheckpointReachedEvent(AGENT))
    observer = factory.created[0]
    event_bus.publish(
        ToolCalledEvent(
            observer.agent_id, "call-1", suggest("data1.txt should be greeting.txt")
        )
    )

    assert agent_input.drain() == [
        "Suggestion from the naming observer:\ndata1.txt should be greeting.txt"
    ]


def test_an_observation_without_a_suggestion_does_not_disturb_the_agent():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    agent_input = Input(DummyUserInput())
    observers_of(event_bus, ["naming"], ChangeReporterStub(DIFF), factory, agent_input)

    event_bus.publish(CheckpointReachedEvent(AGENT))
    observer = factory.created[0]
    event_bus.publish(
        ToolCalledEvent(
            observer.agent_id, "call-1", RawToolCall("complete-task", "looks fine")
        )
    )

    assert agent_input.drain() == []


def test_an_observer_learns_what_the_agent_is_trying_to_do():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    observers_of(
        event_bus,
        ["naming"],
        ChangeReporterStub(DIFF),
        factory,
        intent=IntentStub("Store the greeting"),
    )

    event_bus.publish(CheckpointReachedEvent(AGENT))

    assert factory.created[0].observed == [f"Intent: Store the greeting\n\n{DIFF}"]


def test_an_observer_sees_the_diff_alone_when_no_intent_was_communicated():
    event_bus = SimpleEventBus()
    factory = ObserverFactoryStub()
    observers_of(event_bus, ["naming"], ChangeReporterStub(DIFF), factory)

    event_bus.publish(CheckpointReachedEvent(AGENT))

    assert factory.created[0].observed == [DIFF]
