import re

from simple_agent.application.tool_library import ToolLibrary, MessageAndParsedTools, ParsedTool, Tool
from .bash_tool import BashTool
from .cat_tool import CatTool
from .complete_task_tool import CompleteTaskTool
from .create_file_tool import CreateFileTool
from .edit_file_tool import EditFileTool
from .ls_tool import LsTool
from .subagent_context import SubagentContext
from .subagent_tool import SubagentTool
from .write_todos_tool import WriteTodosTool


class AllTools(ToolLibrary):
    def __init__(
        self,
        subagent_context: SubagentContext | None = None,
        tool_keys: list[str] | None = None
    ):
        self.subagent_context = subagent_context
        self.tool_keys = tool_keys

        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()
        self.tools: list[Tool] = static_tools + dynamic_tools
        self.tool_dict = {getattr(tool, 'name', ''): tool for tool in self.tools}

    def _create_static_tools(self):
        tool_map = {
            'write_todos': lambda: WriteTodosTool(self.subagent_context.agent_id) if self.subagent_context else WriteTodosTool("Agent"),
            'ls': lambda: LsTool(),
            'cat': lambda: CatTool(),
            'create_file': lambda: CreateFileTool(),
            'edit_file': lambda: EditFileTool(),
            'complete_task': lambda: CompleteTaskTool(),
            'bash': lambda: BashTool(),
            'subagent': lambda: SubagentTool(self.subagent_context) if self.subagent_context else None
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
