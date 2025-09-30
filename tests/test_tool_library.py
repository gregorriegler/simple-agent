from tools import ToolLibrary


class TestToolLibrary(ToolLibrary):
    print_fn = None

    @classmethod
    def set_print_fn(cls, print_fn):
        cls.print_fn = print_fn

    def __init__(self, chat):
        super().__init__(chat, print_fn=self.print_fn)
