from simple_agent.application.user_input import UserInput


class UserInputStub(UserInput):
    def __init__(self, inputs=None, escapes=None):
        self._inputs = list(inputs) if inputs is not None else [""]
        self._escapes = list(escapes) if escapes is not None else []
        self._last_escape = False

    async def read_async(self) -> str:
        if not self._inputs:
            return ""
        value = self._inputs.pop(0)
        if callable(value):
            try:
                value = value()
            except TypeError:
                value = value("")
        return str(value).strip()

    def escape_requested(self) -> bool:
        if self._escapes:
            value = self._escapes.pop(0)
            if callable(value):
                value = value()
            self._last_escape = bool(value)
            return self._last_escape
        return self._last_escape

    def close(self) -> None:
        pass
