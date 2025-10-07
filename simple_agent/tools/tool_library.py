import re
import subprocess

from simple_agent.application.io import IO
from simple_agent.application.llm import LLM
from simple_agent.infrastructure.stdio import StdIO
from .bash_tool import BashTool
from .cat_tool import CatTool
from .complete_task_tool import CompleteTaskTool
from .create_file_tool import CreateFileTool
from .edit_file_tool import EditFileTool
from .ls_tool import LsTool
from .patch_file_tool import PatchFileTool
from .recall_tool import RecallTool
from .remember_tool import RememberTool
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


class ToolLibrary:
    def __init__(self, llm: LLM | None = None, indent_level=0, io: IO | None = None):
        if llm is None:
            llm = lambda system_prompt, messages: ''
        self.llm: LLM = llm
        self.indent_level = indent_level
        self.io = io or StdIO()
        
        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()
        self.tools = static_tools + dynamic_tools
        self._build_tool_dict()
        
    def _create_static_tools(self):
        return [
            WriteTodosTool(self.run_command),
            LsTool(self.run_command),
            CatTool(self.run_command),
            CreateFileTool(self.run_command),
            EditFileTool(self.run_command),
            PatchFileTool(self.run_command),
            SubagentTool(self.run_command, self.llm, self.indent_level, self.io),
            RememberTool(self.run_command),
            RecallTool(self.run_command),
            CompleteTaskTool(self.run_command),
            BashTool(self.run_command)
        ]

    def _discover_dynamic_tools(self):
        return []

    def _build_tool_dict(self):
        self.tool_dict = {tool.name: tool for tool in self.tools}

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

    @staticmethod
    def run_command(command, args=None, cwd=None):
        try:
            command_line = [command]
            if args:
                if isinstance(args, str):
                    args = [args]
                command_line += args

            result = subprocess.run(
                command_line,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30,
                cwd=cwd
            )
            output = result.stdout.rstrip('\n')
            if result.stderr:
                if output:
                    output += f"\n";
                output += f"STDERR: {result.stderr}"
            return {
                'output': output
            }
        except subprocess.TimeoutExpired:
            return {'output': 'Command timed out (30s limit)'}
        except Exception as e:
            return {'output': f'Error: {str(e)}'}
