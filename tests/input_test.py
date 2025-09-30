from application.input import Input


class DisplayStub:
    def __init__(self, value="input"):
        self.value = value
        self.calls = 0

    def input(self):
        self.calls += 1
        return self.value

    def escape_requested(self):
        return False


def test_input_uses_display_input_when_stack_empty():
    display = DisplayStub("user input")
    feed = Input(display)

    result = feed.read()

    assert result == "user input"
    assert display.calls == 1


def test_input_returns_stacked_message_before_display():
    display = DisplayStub("user input")
    feed = Input(display)
    feed.stack("stacked")

    result = feed.read()

    assert result == "stacked"
    assert display.calls == 0
