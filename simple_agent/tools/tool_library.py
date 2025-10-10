import re

from simple_agent.application.agent import Agent
from simple_agent.application.io import IO
from simple_agent.application.llm import LLM
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.system_prompt_generator import generate_system_prompt
from simple_agent.application.session_storage import NoOpSessionStorage
from .bash_tool import BashTool
from .cat_tool import CatTool
from .complete_task_tool import CompleteTaskTool
from .create_file_tool import CreateFileTool
from .edit_file_tool import EditFileTool
from .ls_tool import LsTool
from .subagent_tool import SubagentTool
from .write_todos_tool import WriteTodosTool


class ParsedTool:
    def __init__(self, name, arguments, tool_instance):
        self.name = name
        self.arguments = arguments
        self.tool_instance = tool_instance

    def __str__(self):
        if self.arguments:
            return f"🛠️ {self.name} {self.arguments}"
        return f"🛠️ {self.name}"


class AllTools:
    def __init__(self, llm: LLM | None = None, indent_level=0, io: IO | None = None, agent_id: str = "Agent", event_bus=None, display_handler=None):
        if llm is None:
            llm = lambda system_prompt, messages: ''
        self.llm: LLM = llm
        self.indent_level = indent_level
        self.io = io or StdIO()
        self.agent_id = agent_id
        self.event_bus = event_bus
        self.display_handler = display_handler

        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()
        self.tools = static_tools + dynamic_tools
        self._build_tool_dict()

    def _create_static_tools(self):
        return [
            WriteTodosTool(self.agent_id),
            LsTool(),
            CatTool(),
            CreateFileTool(),
            EditFileTool(),
#            PatchFileTool(),
            self._create_subagent_tool(),
#            RememberTool(),
#           RecallTool(),
            CompleteTaskTool(),
            BashTool()
        ]

    def _discover_dynamic_tools(self):
        return []

    def _build_tool_dict(self):
        self.tool_dict = {tool.name: tool for tool in self.tools}

    def _create_subagent_tool(self):
        return SubagentTool(self._build_subagent_agent, self.indent_level, self.io, self.display_handler, self.agent_id)

    def _build_subagent_agent(self, agent_id, user_input, display, display_handler):
        if display_handler:
            display_handler.register_display(agent_id, display)
        subagent_tools = AllTools(self.llm, self.indent_level + 1, self.io, agent_id, self.event_bus, display_handler)
        system_prompt = self._build_system_prompt(subagent_tools)
        session_storage = NoOpSessionStorage()
        return Agent(
            agent_id,
            self.llm,
            system_prompt,
            user_input,
            subagent_tools,
            self.event_bus,
            session_storage
        )

    def _build_system_prompt(self, subagent_tools):
        return lambda tool_library: generate_system_prompt(subagent_tools)

    def get_tool_info(self, tool_name=None):
        if tool_name:
            tool = self.tool_dict.get(tool_name)
            if not tool:
                return f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tool_dict.keys())}"
            if hasattr(tool, 'get_usage_info'):
                return tool.get_usage_info()
            else:
                return f"Tool: {tool.name}\nDescription: {getattr(tool, 'description', 'No description available')}"
        else:
            info_lines = ["Available Tools:"]
            for tool in self.tools:
                description = getattr(tool, 'description', 'No description available')
                info_lines.append(f"  {tool.name}: {description}")
            return "\n".join(info_lines)

    def parse_tool(self, text):
        pattern = r'^🛠️ ([\w-]+)(?:\s+(.*))?'
        lines = text.splitlines(keepends=True)
        for i, line in enumerate(lines):
            match = re.match(pattern, line, re.DOTALL)
            if match:
                command, same_line_args = match.groups()
                tool = self.tool_dict.get(command)
                if not tool:
                    return None
                all_arg_lines = []
                if same_line_args: all_arg_lines.append(same_line_args)
                for j in range(i + 1, len(lines)):
                    if re.match(r'^🛠️ ', lines[j]):
                        break
                    all_arg_lines.append(lines[j])
                arguments = ''.join(all_arg_lines)
                return ParsedTool(command, arguments, tool)
        return None

    def execute_parsed_tool(self, parsed_tool):
        args = parsed_tool.arguments if parsed_tool.arguments else None
        result = parsed_tool.tool_instance.execute(args)
        return result

