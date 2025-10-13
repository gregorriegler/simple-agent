import re
from typing import Callable, Any

from simple_agent.application.agent import Agent
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM
from simple_agent.application.session_storage import NoOpSessionStorage
from simple_agent.application.tool_library import ToolLibrary, MessageAndParsedTools, ParsedTool, Tool
from simple_agent.system_prompt_generator import generate_system_prompt
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
        create_subagent_input: Callable[[int], Input] | None = None
    ):
        from simple_agent.application.event_bus import SimpleEventBus

        self.llm: LLM = llm if llm is not None else (lambda system_prompt, messages: '')
        self.indent_level = indent_level
        self.agent_id = agent_id
        self.event_bus: EventBus = event_bus if event_bus is not None else SimpleEventBus()
        self.user_input = user_input

        assert create_subagent_display is not None, "create_subagent_display must be provided"
        assert create_subagent_input is not None, "create_subagent_input must be provided"

        self.create_subagent_display = create_subagent_display
        self.create_subagent_input = create_subagent_input

        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()
        self.tools: list[Tool] = static_tools + dynamic_tools + [self._create_subagent_tool()]
        self.tool_dict = {getattr(tool, 'name', ''): tool for tool in self.tools}

    def _create_static_tools(self):
        return [
            WriteTodosTool(self.agent_id),
            LsTool(),
            CatTool(),
            CreateFileTool(),
            EditFileTool(),
            #            PatchFileTool(),
            #            RememberTool(),
            #           RecallTool(),
            CompleteTaskTool(),
            BashTool()
        ]

    def _discover_dynamic_tools(self):
        return []

    def _create_subagent_tool(self):
        return SubagentTool(
            self._create_default_agent,
            self.create_subagent_display,
            self.indent_level,
            self.agent_id,
            self.create_subagent_input
        )

    def _create_default_agent(
        self,
        agent_id,
        user_input,
        session_storage=NoOpSessionStorage()
    ) -> Agent:
        subagent_tools = AllTools(
            self.llm,
            self.indent_level + 1,
            agent_id,
            self.event_bus,
            self.user_input,
            self.create_subagent_display,
            self.create_subagent_input
        )
        system_prompt = self._build_system_prompt(subagent_tools)
        return Agent(
            agent_id,
            system_prompt,
            subagent_tools,
            self.llm,
            user_input,
            self.event_bus,
            session_storage
        )

    def _build_system_prompt(self, subagent_tools) -> Callable[[Any], str]:
        return lambda tool_library: generate_system_prompt(subagent_tools)

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
