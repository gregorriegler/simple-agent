from typing import Callable, List

from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library import ToolLibrary, MessageAndParsedTools, ParsedTool, Tool
from simple_agent.application.tool_message_parser import parse_tool_calls, CURRENT_SYNTAX
from simple_agent.application.tool_library_factory import ToolLibraryFactory, ToolContext
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
        tool_context: ToolContext,
        spawner: SubagentSpawner,
        get_agent_types: Callable[[], List[str]] = None
    ):
        self.tool_context = tool_context
        self._spawner = spawner
        self._get_agent_types = get_agent_types or (lambda: [])
        self.tool_keys = tool_context.tool_keys if tool_context.tool_keys else []

        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()
        self.tools: list[Tool] = static_tools + dynamic_tools
        self.tool_dict = {getattr(tool, 'name', ''): tool for tool in self.tools}

    def _create_static_tools(self):
        tool_map = {
            'write_todos': lambda: WriteTodosTool(self.tool_context.agent_id.todo_filename()),
            'ls': lambda: LsTool(),
            'cat': lambda: CatTool(),
            'create_file': lambda: CreateFileTool(),
            'edit_file': lambda: EditFileTool(),
            'complete_task': lambda: CompleteTaskTool(),
            'bash': lambda: BashTool(),
            'subagent': lambda: SubagentTool(self._spawner, self._get_agent_types)
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
        parsed = parse_tool_calls(text, CURRENT_SYNTAX)

        tools = []
        for raw_call in parsed.tool_calls:
            tool_instance = self.tool_dict.get(raw_call.name)
            if not tool_instance:
                # Unknown tool - return message as-is with no tools
                return MessageAndParsedTools(message=text, tools=[])
            tools.append(ParsedTool(raw_call.name, raw_call.arguments, tool_instance))

        return MessageAndParsedTools(message=parsed.message, tools=tools)

    def execute_parsed_tool(self, parsed_tool):
        args = parsed_tool.arguments if parsed_tool.arguments else None
        result = parsed_tool.tool_instance.execute(args)
        return result

    def _discover_dynamic_tools(self):
        return []


class AllToolsFactory(ToolLibraryFactory):
    def create(
        self,
        tool_context: ToolContext,
        spawner: SubagentSpawner,
        get_agent_types: Callable[[], List[str]] = None
    ) -> ToolLibrary:
        return AllTools(tool_context, spawner, get_agent_types)
