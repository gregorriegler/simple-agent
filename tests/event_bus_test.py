import pytest
from simple_agent.application.event_bus import SimpleEventBus


class TestSimpleEventBus:

    def test_subscribe_adds_handler_for_event_type(self):
        event_bus = SimpleEventBus()
        handler = lambda data: None

        event_bus.subscribe("test_event", handler)

        assert "test_event" in event_bus._handlers
        assert handler in event_bus._handlers["test_event"]

    def test_subscribe_multiple_handlers_for_same_event_type(self):
        event_bus = SimpleEventBus()
        handler1 = lambda data: None
        handler2 = lambda data: None

        event_bus.subscribe("test_event", handler1)
        event_bus.subscribe("test_event", handler2)

        assert len(event_bus._handlers["test_event"]) == 2
        assert handler1 in event_bus._handlers["test_event"]
        assert handler2 in event_bus._handlers["test_event"]

    def test_unsubscribe_removes_handler_from_event_type(self):
        event_bus = SimpleEventBus()
        handler = lambda data: None
        event_bus.subscribe("test_event", handler)

        event_bus.unsubscribe("test_event", handler)

        assert "test_event" not in event_bus._handlers

    def test_unsubscribe_removes_only_specified_handler(self):
        event_bus = SimpleEventBus()
        handler1 = lambda data: None
        handler2 = lambda data: None
        event_bus.subscribe("test_event", handler1)
        event_bus.subscribe("test_event", handler2)

        event_bus.unsubscribe("test_event", handler1)

        assert len(event_bus._handlers["test_event"]) == 1
        assert handler2 in event_bus._handlers["test_event"]

    def test_unsubscribe_nonexistent_handler_does_not_raise_error(self):
        event_bus = SimpleEventBus()
        handler = lambda data: None

        event_bus.unsubscribe("test_event", handler)

        assert "test_event" not in event_bus._handlers

    def test_unsubscribe_handler_not_in_list_does_not_raise_error(self):
        event_bus = SimpleEventBus()
        handler1 = lambda data: None
        handler2 = lambda data: None
        event_bus.subscribe("test_event", handler1)

        event_bus.unsubscribe("test_event", handler2)

        assert handler1 in event_bus._handlers["test_event"]

    def test_publish_calls_all_subscribed_handlers(self):
        event_bus = SimpleEventBus()
        results = []
        handler1 = lambda data: results.append(f"handler1: {data}")
        handler2 = lambda data: results.append(f"handler2: {data}")
        event_bus.subscribe("test_event", handler1)
        event_bus.subscribe("test_event", handler2)

        event_bus.publish("test_event", "test_data")

        assert len(results) == 2
        assert "handler1: test_data" in results
        assert "handler2: test_data" in results

    def test_publish_with_no_data_passes_none_to_handlers(self):
        event_bus = SimpleEventBus()
        received_data = []
        handler = lambda data: received_data.append(data)
        event_bus.subscribe("test_event", handler)

        event_bus.publish("test_event")

        assert received_data[0] is None

    def test_publish_nonexistent_event_type_does_nothing(self):
        event_bus = SimpleEventBus()

        event_bus.publish("nonexistent_event", "data")

        assert len(event_bus._handlers) == 0

    def test_publish_passes_event_data_to_handlers(self):
        event_bus = SimpleEventBus()
        received_data = []
        handler = lambda data: received_data.append(data)
        event_bus.subscribe("test_event", handler)
        test_data = {"key": "value", "number": 42}

        event_bus.publish("test_event", test_data)

        assert received_data[0] == test_data
