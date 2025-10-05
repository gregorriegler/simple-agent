class IOSpy:
    def __init__(self, inputs=None, interrupts=None):
        self._inputs = []
        self._escape_responses = []
        self._escape_last = False
        self.outputs = []
        self.prompts = []
        if inputs is not None:
            self.set_inputs(inputs)
        if interrupts is not None:
            self.set_escape_responses(interrupts)

    def set_inputs(self, inputs):
        self._inputs = list(inputs)

    def input(self, prompt: str) -> str:
        self.outputs.append(prompt)
        if not self._inputs:
            return ""
        value = self._inputs.pop(0)
        if callable(value):
            result = value(prompt)
            return str(result) if result is not None else ""
        if isinstance(value, str):
            return value
        return str(value)

    def print(self, message, *, file=None):
        self.outputs.append(str(message))

    def get_output(self):
        return "\n".join(self.outputs)

    def set_escape_responses(self, responses):
        self._escape_responses = list(responses)
        self._escape_last = False

    def escape_requested(self):
        if self._escape_responses:
            value = self._escape_responses.pop(0)
            if callable(value):
                value = value()
            self._escape_last = bool(value)
            return self._escape_last
        return self._escape_last
