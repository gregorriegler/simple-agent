import re
from typing import Callable, Any

from simple_agent.application.agent_factory import CreateAgent
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM
from simple_agent.application.tool_library import ToolLibrary, MessageAndParsedTools, ParsedTool, Tool
from .bash_tool import BashTool
from .cat_tool import CatTool
from .complete_task_tool import CompleteTaskTool
from .create_file_tool import CreateFileTool
from .edit_file_tool import EditFileTool
from .ls_tool import LsTool
from .subagent_tool import SubagentTool
from .write_todos_tool import WriteTodosTool


class AllTools(ToolLibrary):
    def __init__(
        self,
        llm: LLM | None = None,
        indent_level=0,
        agent_id: str = "Agent",
        event_bus: EventBus | None = None,
        user_input=None,
        create_subagent_display: Callable[[str, int], Any] | None = None,
        create_subagent_input: Callable[[int], Input] | None = None,
        create_agent: CreateAgent | None = None,
        tool_keys: list[str] | None = None
    ):
        from simple_agent.application.event_bus import SimpleEventBus

        self.llm: LLM = llm if llm is not None else (lambda system_prompt, messages: '')
        self.indent_level = indent_level
        self.agent_id = agent_id
        self.event_bus: EventBus = event_bus if event_bus is not None else SimpleEventBus()
        self.user_input = user_input
        self.create_subagent_display = create_subagent_display
        self.create_subagent_input = create_subagent_input

        self.create_agent = create_agent
        self.tool_keys = tool_keys

        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()
        self.tools: list[Tool] = static_tools + dynamic_tools
        self.tool_dict = {getattr(tool, 'name', ''): tool for tool in self.tools}

    def _create_static_tools(self):
        tool_map = {
            'write_todos': lambda: WriteTodosTool(self.agent_id),
            'ls': lambda: LsTool(),
            'cat': lambda: CatTool(),
            'create_file': lambda: CreateFileTool(),
            'edit_file': lambda: EditFileTool(),
            'complete_task': lambda: CompleteTaskTool(),
            'bash': lambda: BashTool(),
            'subagent': lambda: SubagentTool(
                self.create_agent,
                self.create_subagent_display,
                self.indent_level + 1,
                self.agent_id,
                self.create_subagent_input
            ) if self.create_agent else None
        }

        if not self.tool_keys:
            tools = [factory() for factory in tool_map.values()]
            return [tool for tool in tools if tool is not None]

        tools = []
        for key in self.tool_keys:
            if key in tool_map:
                tool = tool_map[key]()
                if tool is not None:
                    tools.append(tool)
        return tools

    def parse_message_and_tools(self, text) -> MessageAndParsedTools:
        pattern = r'^🛠️ ([\w-]+)(?:\s+(.*))?'
        end_marker = r'^🛠️🔚'
        lines = text.splitlines(keepends=True)
        parsed_tools = []
        message = ""
        first_tool_index = None

        i = 0
        while i < len(lines):
            match = re.match(pattern, lines[i], re.DOTALL)
            if match:
                if first_tool_index is None:
                    first_tool_index = i
                    message = ''.join(lines[:i]).rstrip()

                command, same_line_args = match.groups()
                tool = self.tool_dict.get(command)
                if not tool:
                    return MessageAndParsedTools(message=text, tools=[])

                all_arg_lines = []
                if same_line_args:
                    all_arg_lines.append(same_line_args)

                i += 1
                while i < len(lines) and not re.match(r'^🛠️ ', lines[i]) and not re.match(end_marker, lines[i]):
                    all_arg_lines.append(lines[i])
                    i += 1

                if i < len(lines) and re.match(end_marker, lines[i]):
                    i += 1

                arguments = ''.join(all_arg_lines).rstrip()
                parsed_tools.append(ParsedTool(command, arguments, tool))
            else:
                i += 1

        if parsed_tools:
            return MessageAndParsedTools(message=message, tools=parsed_tools)
        return MessageAndParsedTools(message=text, tools=[])

    def execute_parsed_tool(self, parsed_tool):
        args = parsed_tool.arguments if parsed_tool.arguments else None
        result = parsed_tool.tool_instance.execute(args)
        return result

    def _discover_dynamic_tools(self):
        return []
