import re

from simple_agent.application.agent import Agent
from simple_agent.application.display import Display
from simple_agent.application.io import IO
from simple_agent.application.llm import LLM
from simple_agent.application.session_storage import NoOpSessionStorage
from simple_agent.application.tool_library import ToolLibrary, MessageAndParsedTools, ParsedTool
from simple_agent.infrastructure.console_display import ConsoleDisplay
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.infrastructure.textual_display import TextualDisplay
from simple_agent.system_prompt_generator import generate_system_prompt
from .bash_tool import BashTool
from .cat_tool import CatTool
from .complete_task_tool import CompleteTaskTool
from .create_file_tool import CreateFileTool
from .edit_file_tool import EditFileTool
from .ls_tool import LsTool
from .subagent_tool import SubagentTool
from .write_todos_tool import WriteTodosTool
from simple_agent.application.input import Input
from simple_agent.infrastructure.console_user_input import ConsoleUserInput


class SubagentConsoleDisplay(ConsoleDisplay):
    def __init__(self, indent_level=1, io: IO | None = None):
        super().__init__(indent_level, "Subagent", io)

    def exit(self):
        pass


class SubagentTextualDisplay(TextualDisplay):
    def __init__(self):
        super().__init__("Subagent")

    def exit(self):
        pass


class AllTools(ToolLibrary):
    def __init__(
        self,
        llm: LLM | None = None,
        indent_level=0,
        io: IO | None = None,
        agent_id: str = "Agent",
        event_bus=None,
        display_event_handler=None
    ):
        if llm is None:
            llm = lambda system_prompt, messages: ''
        self.llm: LLM = llm
        self.indent_level = indent_level
        self.io = io or StdIO()
        self.agent_id = agent_id
        self.event_bus = event_bus
        self.display_event_handler = display_event_handler

        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()
        self.tools = static_tools + dynamic_tools + [self._create_subagent_tool()]
        self.tool_dict = {tool.name: tool for tool in self.tools}

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
            self._create_agent,
            self._create_subagent_display,
            self.indent_level,
            self.agent_id,
            self.display_event_handler,
            Input(ConsoleUserInput(self.indent_level + 1, self.io))
        )

    def _create_subagent_display(self) -> Display:
        if self.display_event_handler:
            parent_display = self.display_event_handler.displays.get("Agent")
            if isinstance(parent_display, TextualDisplay):
                return SubagentTextualDisplay()
        return SubagentConsoleDisplay(self.indent_level + 1, self.io)

    def _create_agent(
        self,
        agent_id,
        user_input,
        display_event_handler
    ):
        subagent_tools = AllTools(
            self.llm,
            self.indent_level + 1,
            self.io,
            agent_id,
            self.event_bus,
            display_event_handler
        )
        system_prompt = self._build_system_prompt(subagent_tools)
        session_storage = NoOpSessionStorage()
        return Agent(
            agent_id,
            system_prompt,
            subagent_tools,
            self.llm,
            user_input,
            self.event_bus,
            session_storage
        )

    def _build_system_prompt(self, subagent_tools):
        return lambda tool_library: generate_system_prompt(subagent_tools)

    def parse_tool(self, text):
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
                    return None

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
