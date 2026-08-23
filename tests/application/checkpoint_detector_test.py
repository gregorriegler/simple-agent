from simple_agent.application.agent_id import AgentId
from simple_agent.application.checkpoint_detector import CheckpointDetector
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    CheckpointReachedEvent,
    ToolCalledEvent,
    ToolResultEvent,
)
from simple_agent.application.tool_library import RawToolCall
from simple_agent.application.tool_results import SingleToolResult

AGENT = AgentId("Agent")


def write_file(event_bus, call_id):
    event_bus.publish(
        ToolCalledEvent(AGENT, call_id, RawToolCall("create-file", "some.py"))
    )
    event_bus.publish(ToolResultEvent(AGENT, call_id, SingleToolResult("created")))


def record_checkpoints(event_bus):
    checkpoints = []
    event_bus.subscribe(CheckpointReachedEvent, checkpoints.append)
    return checkpoints


def test_no_checkpoint_while_an_observer_round_is_in_flight():
    event_bus = SimpleEventBus()
    detector = CheckpointDetector(event_bus)
    checkpoints = record_checkpoints(event_bus)

    detector.round_started()
    write_file(event_bus, "call-1")

    assert len(checkpoints) == 0


def test_checkpoints_again_once_the_round_finished():
    event_bus = SimpleEventBus()
    detector = CheckpointDetector(event_bus)
    checkpoints = record_checkpoints(event_bus)

    detector.round_started()
    detector.round_finished()
    write_file(event_bus, "call-1")

    assert len(checkpoints) == 1
