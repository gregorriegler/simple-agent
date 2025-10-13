import re
from typing import Callable, Any

from simple_agent.application.agent import Agent
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.io import IO
from simple_agent.application.llm import LLM
from simple_agent.application.session_storage import NoOpSessionStorage
from simple_agent.application.tool_library import ToolLibrary, MessageAndParsedTools, ParsedTool, Tool
from simple_agent.infrastructure.console_display import ConsoleDisplay
from simple_agent.infrastructure.console_user_input import ConsoleUserInput
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


class SubagentConsoleDisplay(ConsoleDisplay):
    def __init__(self, indent_level=1, io: IO | None = None):
        super().__init__(indent_level, "Subagent", io)

    def exit(self):
        pass


class SubagentTextualDisplay(TextualDisplay):
    def __init__(self, parent_app, agent_id: str):
        super().__init__("Subagent")
        self.app = parent_app
        self.agent_id = agent_id
        self.log_id = None
        self.tool_results_id = None
        self._create_tab()

    def _create_tab(self):
        if self.app and self.app.is_running:
            tab_title = self.agent_id.split('/')[-1]
            self.log_id, self.tool_results_id = self.app.call_from_thread(
                self.app.add_subagent_tab,
                self.agent_id,
                tab_title
            )

    def user_says(self, message):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_to_tab, self.log_id, f"\nUser: {message}")

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines and self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_to_tab, self.log_id, f"\n{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                self.app.call_from_thread(self.app.write_to_tab, self.log_id, line)

    def tool_call(self, tool):
        if self.app and self.app.is_running and self.tool_results_id:
            self.app.call_from_thread(self.app.write_tool_result_to_tab, self.tool_results_id, str(tool) + "\n")

    def tool_result(self, result):
        if not result:
            return
        lines = str(result).split('\n')
        if self.app and self.app.is_running and self.tool_results_id:
            for line in lines:
                self.app.call_from_thread(self.app.write_tool_result_to_tab, self.tool_results_id, line)
            self.app.call_from_thread(self.app.write_tool_result_to_tab, self.tool_results_id, "---")

    def continue_session(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_to_tab, self.log_id, "Continuing session")

    def start_new_session(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_to_tab, self.log_id, "Starting new session")

    def waiting_for_input(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_to_tab, self.log_id, "\nWaiting for user input...")

    def interrupted(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_to_tab, self.log_id, "\n[Session interrupted by user]")

    def exit(self):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.remove_subagent_tab, self.agent_id)


class AllTools(ToolLibrary):
    def __init__(
        self,
        llm: LLM | None = None,
        indent_level=0,
        io: IO | None = None,
        agent_id: str = "Agent",
        event_bus: EventBus | None = None,
        display_event_handler=None,
        user_input=None
    ):
        from simple_agent.application.event_bus import SimpleEventBus

        self.llm: LLM = llm if llm is not None else (lambda system_prompt, messages: '')
        self.indent_level = indent_level
        self.io = io or StdIO()
        self.agent_id = agent_id
        self.event_bus: EventBus = event_bus if event_bus is not None else SimpleEventBus()
        self.display_event_handler = display_event_handler
        self.user_input = user_input

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
        subagent_input = self._create_subagent_input()
        return SubagentTool(
            self._create_main_agent,
            self._create_subagent_display,
            self.indent_level,
            self.agent_id,
            self.display_event_handler,
            subagent_input
        )

    def _create_subagent_input(self):
        if self.user_input and hasattr(self.user_input, 'user_input'):
            from simple_agent.infrastructure.textual_user_input import TextualUserInput
            if isinstance(self.user_input.user_input, TextualUserInput):
                return self.user_input
        return Input(ConsoleUserInput(self.indent_level + 1, self.io))

    def _create_subagent_display(self, agent_id: str):
        if self.display_event_handler:
            parent_display = self.display_event_handler.displays.get("Agent")
            if isinstance(parent_display, TextualDisplay):
                return SubagentTextualDisplay(parent_display.app, agent_id)
        return SubagentConsoleDisplay(self.indent_level + 1, self.io)

    def _create_main_agent(
        self,
        agent_id,
        user_input,
        display_event_handler,
        session_storage=NoOpSessionStorage()
    ) -> Agent:
        subagent_tools = AllTools(
            self.llm,
            self.indent_level + 1,
            self.io,
            agent_id,
            self.event_bus,
            display_event_handler,
            self.user_input
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
