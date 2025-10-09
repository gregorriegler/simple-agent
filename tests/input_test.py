from simple_agent.application.input import Input


class UserInputStub:
    def __init__(self, value="input"):
        self.value = value
        self.calls = 0

    def read(self):
        self.calls += 1
        return self.value

    def escape_requested(self):
        return False


def test_input_uses_display_input_when_stack_empty():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)

    result = feed.read()

    assert result == "user input"
    assert user_input_port.calls == 1


def test_input_returns_stacked_message_before_display():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)
    feed.stack("stacked")

    result = feed.read()

    assert result == "stacked"
    assert user_input_port.calls == 0
