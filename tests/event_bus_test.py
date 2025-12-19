from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import AssistantSaidEvent, ToolResultEvent
from simple_agent.application.tool_results import ContinueResult


class TestSimpleEventBus:

    def test_subscribe_adds_handler_for_event_type(self):
        event_bus = SimpleEventBus()
        handler = lambda event: None

        event_bus.subscribe(AssistantSaidEvent, handler)

        assert AssistantSaidEvent in event_bus._handlers
        assert handler in event_bus._handlers[AssistantSaidEvent]

    def test_subscribe_multiple_handlers_for_same_event_type(self):
        event_bus = SimpleEventBus()
        handler1 = lambda event: None
        handler2 = lambda event: None

        event_bus.subscribe(AssistantSaidEvent, handler1)
        event_bus.subscribe(AssistantSaidEvent, handler2)

        assert len(event_bus._handlers[AssistantSaidEvent]) == 2
        assert handler1 in event_bus._handlers[AssistantSaidEvent]
        assert handler2 in event_bus._handlers[AssistantSaidEvent]

    def test_unsubscribe_removes_handler_from_event_type(self):
        event_bus = SimpleEventBus()
        handler = lambda event: None
        event_bus.subscribe(AssistantSaidEvent, handler)

        event_bus.unsubscribe(AssistantSaidEvent, handler)

        assert AssistantSaidEvent not in event_bus._handlers

    def test_unsubscribe_removes_only_specified_handler(self):
        event_bus = SimpleEventBus()
        handler1 = lambda event: None
        handler2 = lambda event: None
        event_bus.subscribe(AssistantSaidEvent, handler1)
        event_bus.subscribe(AssistantSaidEvent, handler2)

        event_bus.unsubscribe(AssistantSaidEvent, handler1)

        assert len(event_bus._handlers[AssistantSaidEvent]) == 1
        assert handler2 in event_bus._handlers[AssistantSaidEvent]

    def test_unsubscribe_nonexistent_handler_does_not_raise_error(self):
        event_bus = SimpleEventBus()
        handler = lambda event: None

        event_bus.unsubscribe(AssistantSaidEvent, handler)

        assert AssistantSaidEvent not in event_bus._handlers

    def test_unsubscribe_handler_not_in_list_does_not_raise_error(self):
        event_bus = SimpleEventBus()
        handler1 = lambda event: None
        handler2 = lambda event: None
        event_bus.subscribe(AssistantSaidEvent, handler1)

        event_bus.unsubscribe(AssistantSaidEvent, handler2)

        assert handler1 in event_bus._handlers[AssistantSaidEvent]

    def test_publish_calls_all_subscribed_handlers(self):
        event_bus = SimpleEventBus()
        results = []
        handler1 = lambda event: results.append(("handler1", event))
        handler2 = lambda event: results.append(("handler2", event))
        event_bus.subscribe(AssistantSaidEvent, handler1)
        event_bus.subscribe(AssistantSaidEvent, handler2)

        event = AssistantSaidEvent("agent", "test_data")
        event_bus.publish(event)

        assert len(results) == 2
        assert ("handler1", event) in results
        assert ("handler2", event) in results

    def test_publish_with_no_data_passes_none_to_handlers(self):
        event_bus = SimpleEventBus()
        received_data = []
        handler = lambda event: received_data.append(event)
        event_bus.subscribe(AssistantSaidEvent, handler)

        event = AssistantSaidEvent("agent", "message")
        event_bus.publish(event)

        assert received_data[0] == event

    def test_publish_nonexistent_event_type_does_nothing(self):
        event_bus = SimpleEventBus()

        event_bus.publish(ToolResultEvent("agent", "call-1", ContinueResult("data")))

        assert len(event_bus._handlers) == 0

    def test_publish_passes_event_data_to_handlers(self):
        event_bus = SimpleEventBus()
        received_data = []
        handler = lambda event: received_data.append(event)
        event_bus.subscribe(AssistantSaidEvent, handler)
        event = AssistantSaidEvent("agent", "test_data")

        event_bus.publish(event)

        assert received_data[0] == event
