from simple_agent.tools import ToolLibrary


class TestToolLibrary(ToolLibrary):
    def __init__(self, llm, io=None, interrupts=None):
        super().__init__(llm, io=io)
        self.interrupts = interrupts or []
        self.counter = 0

    def execute_parsed_tool(self, parsed_tool):
        if self.interrupts and self.counter < len(self.interrupts) and self.interrupts[self.counter]:
            self.counter += 1
            raise KeyboardInterrupt()
        args = parsed_tool.arguments if parsed_tool.arguments else None
        result = parsed_tool.tool_instance.execute(args)
        self.counter += 1
        return result
