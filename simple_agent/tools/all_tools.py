from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library import (
    MessageAndParsedTools,
    ParsedTool,
    Tool,
    ToolLibrary,
)
from simple_agent.application.tool_library_factory import (
    ToolContext,
    ToolLibraryFactory,
)
from simple_agent.application.tool_message_parser import parse_tool_calls
from simple_agent.application.tool_syntax import ToolSyntax

from .bash_tool import BashTool
from .cat_tool import CatTool
from .complete_task_tool import CompleteTaskTool
from .create_file_tool import CreateFileTool
from .ls_tool import LsTool
from .replace_file_content_tool import ReplaceFileContentTool
from .subagent_tool import SubagentTool
from .write_todos_tool import WriteTodosTool


class AllTools(ToolLibrary):
    def __init__(
        self,
        tool_context: ToolContext,
        spawner: SubagentSpawner,
        agent_types: AgentTypes,
        tool_syntax: ToolSyntax,
    ):
        self.tool_context = tool_context
        self._spawner = spawner
        self._agent_types = agent_types
        self.tool_syntax = tool_syntax
        self.tool_keys = tool_context.tool_keys if tool_context.tool_keys else []

        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()
        self.tools: list[Tool] = static_tools + dynamic_tools
        self.tool_dict = {getattr(tool, "name", ""): tool for tool in self.tools}

    def _create_static_tools(self):
        tool_map = {
            "write_todos": lambda: WriteTodosTool(
                self.tool_context.agent_id.todo_filename()
            ),
            "ls": lambda: LsTool(),
            "cat": lambda: CatTool(),
            "create_file": lambda: CreateFileTool(),
            "replace_file_content": lambda: ReplaceFileContentTool(),
            "complete_task": lambda: CompleteTaskTool(),
            "bash": lambda: BashTool(),
            "subagent": lambda: SubagentTool(self._spawner, self._agent_types),
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
        parsed = parse_tool_calls(text, self.tool_syntax)

        tools = []
        for raw_call in parsed.tool_calls:
            tool_instance = self.tool_dict.get(raw_call.name)
            if not tool_instance:
                return MessageAndParsedTools(message=text, tools=[])
            tools.append(ParsedTool(raw_call, tool_instance))

        return MessageAndParsedTools(message=parsed.message, tools=tools)

    async def execute_parsed_tool(self, parsed_tool):
        return await parsed_tool.tool_instance.execute(parsed_tool.raw_call)

    def _discover_dynamic_tools(self):
        return []


class AllToolsFactory(ToolLibraryFactory):
    def __init__(self, tool_syntax: ToolSyntax):
        self.tool_syntax = tool_syntax

    def create(
        self,
        tool_context: ToolContext,
        spawner: SubagentSpawner,
        agent_types: AgentTypes,
    ) -> ToolLibrary:
        return AllTools(tool_context, spawner, agent_types, self.tool_syntax)
