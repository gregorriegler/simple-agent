from tools import ToolLibrary


class TestToolLibrary(ToolLibrary):
    io = None

    @classmethod
    def set_io(cls, io):
        cls.io = io

    def __init__(self, llm):
        super().__init__(llm, io=type(self).io)
