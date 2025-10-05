from simple_agent.tools import ToolLibrary


class TestToolLibrary(ToolLibrary):
    io = None
    interrupts = []
    counter = 0

    @classmethod
    def set_io(cls, io):
        cls.io = io

    @classmethod
    def set_interrupts(cls, interrupts):
        cls.counter = 0
        cls.interrupts = interrupts

    def __init__(self, llm):
        super().__init__(llm, io=type(self).io)

    @staticmethod
    def execute_parsed_tool(parsed_tool):
        if TestToolLibrary.interrupts and TestToolLibrary.interrupts[TestToolLibrary.counter]:
            raise KeyboardInterrupt()
        args = parsed_tool.arguments if parsed_tool.arguments else None
        result = parsed_tool.tool_instance.execute(args)
        TestToolLibrary.counter+=1
        return result
