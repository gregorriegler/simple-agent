from tools import ToolLibrary


class TestToolLibrary(ToolLibrary):
    input_fn = None
    print_fn = None

    @classmethod
    def set_input_fn(cls, input_fn):
        cls.input_fn = input_fn

    @classmethod
    def set_print_fn(cls, print_fn):
        cls.print_fn = print_fn

    def __init__(self, llm):
        super().__init__(llm, input_fn=type(self).input_fn, print_fn=self.print_fn)
