class IOSpy:
    def __init__(self, inputs=None):
        self._inputs = []
        self.outputs = []
        self.prompts = []
        if inputs is not None:
            self.set_inputs(inputs)

    def set_inputs(self, inputs):
        self._inputs = list(inputs)

    def input(self, prompt):
        self.prompts.append(prompt)
        if not self._inputs:
            return ""
        value = self._inputs.pop(0)
        if callable(value):
            return value(prompt)
        if isinstance(value, str):
            return value
        return str(value)

    def print(self, message, *, file=None):
        self.outputs.append(str(message))

    def get_output(self):
        return "\n".join(self.outputs)
