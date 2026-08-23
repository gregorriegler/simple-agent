from .event_bus import EventBus
from .events import CheckpointReachedEvent, ToolCalledEvent, ToolResultEvent

MUTATING_TOOLS = ("create-file", "replace-file-content")


class CheckpointDetector:
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._called_tools: dict[str, str] = {}
        self._round_in_flight = False
        event_bus.subscribe(ToolCalledEvent, self._remember_call)
        event_bus.subscribe(ToolResultEvent, self._check_for_checkpoint)

    def round_started(self) -> None:
        self._round_in_flight = True

    def round_finished(self) -> None:
        self._round_in_flight = False

    def _remember_call(self, event: ToolCalledEvent) -> None:
        if event.call:
            self._called_tools[event.call_id] = event.call.name

    def _check_for_checkpoint(self, event: ToolResultEvent) -> None:
        tool_name = self._called_tools.pop(event.call_id, None)
        if tool_name not in MUTATING_TOOLS:
            return
        if not event.result or not event.result.success:
            return
        if self._round_in_flight:
            return
        self._event_bus.publish(CheckpointReachedEvent(event.agent_id))
