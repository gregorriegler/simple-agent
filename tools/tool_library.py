import re
import subprocess

from application.chat import Chat

from .ls_tool import LsTool
from .cat_tool import CatTool
from .create_file_tool import CreateFileTool
from .edit_file_tool import EditFileTool
from .subagent_tool import SubagentTool
from .complete_task_tool import CompleteTaskTool
from .bash_tool import BashTool


class ParsedTool:
    def __init__(self, name, arguments, tool_instance):
        self.name = name
        self.arguments = arguments
        self.tool_instance = tool_instance

    def is_completing(self):
        return self.tool_instance.is_completing()

    def __str__(self):
        if self.arguments:
            return f"🛠️ {self.name} {self.arguments}"
        return f"🛠️ {self.name}"


class ToolLibrary:
    def __init__(self, message_claude: Chat | None = None, indent_level=0, print_fn=print):
        if message_claude is None:
            message_claude = lambda system_prompt, messages: ''
        self.message_claude: Chat = message_claude
        self.indent_level = indent_level
        self.print_fn = print_fn
        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()

        self.tools = static_tools + dynamic_tools
        self._build_tool_dict()

    def _create_static_tools(self):
        return [
            LsTool(self.run_command),
            CatTool(self.run_command),
            CreateFileTool(self.run_command),
            EditFileTool(self.run_command),
            SubagentTool(self.run_command, self.message_claude, self.indent_level, self.print_fn),
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

    @staticmethod
    def execute_parsed_tool(parsed_tool):
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
                capture_output=True,
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
