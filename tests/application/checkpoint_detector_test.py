from simple_agent.application.agent_id import AgentId
from simple_agent.application.checkpoint_detector import CheckpointDetector
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    CheckpointReachedEvent,
    ToolCalledEvent,
    ToolResultEvent,
)
from simple_agent.application.tool_library import RawToolCall
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus

AGENT = AgentId("Agent")


class CheckpointSpy:
    def __init__(self, event_bus):
        self.events = []
        event_bus.subscribe(CheckpointReachedEvent, self.events.append)

    def __len__(self):
        return len(self.events)


def call_tool(event_bus, name, status=ToolResultStatus.SUCCESS, call_id="call-1"):
    event_bus.publish(ToolCalledEvent(AGENT, call_id, RawToolCall(name, "some.py")))
    event_bus.publish(
        ToolResultEvent(AGENT, call_id, SingleToolResult("done", status=status))
    )


def test_reaches_checkpoint_after_a_file_was_created():
    event_bus = SimpleEventBus()
    CheckpointDetector(event_bus)
    checkpoints = CheckpointSpy(event_bus)

    call_tool(event_bus, "create-file")

    assert len(checkpoints) == 1


def test_no_checkpoint_when_the_write_failed():
    event_bus = SimpleEventBus()
    CheckpointDetector(event_bus)
    checkpoints = CheckpointSpy(event_bus)

    call_tool(event_bus, "create-file", status=ToolResultStatus.FAILURE)

    assert len(checkpoints) == 0


def test_no_checkpoint_for_reading_tools():
    event_bus = SimpleEventBus()
    CheckpointDetector(event_bus)
    checkpoints = CheckpointSpy(event_bus)

    call_tool(event_bus, "cat")

    assert len(checkpoints) == 0
