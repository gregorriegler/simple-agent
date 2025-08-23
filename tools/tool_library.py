import re
import subprocess

from .ls_tool import LsTool
from .cat_tool import CatTool
from .create_file_tool import CreateFileTool
from .edit_file_tool import EditFileTool


class ToolLibrary:
    def __init__(self):
        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()

        self.tools = static_tools + dynamic_tools
        self._build_tool_dict()

    def _create_static_tools(self):
        """Create the core static tools that are always available."""
        return [
            LsTool(self.run_command),
            CatTool(self.run_command),
            CreateFileTool(self.run_command),
            EditFileTool(self.run_command)
        ]

    def _discover_dynamic_tools(self):
        """Discover and create dynamic tools from external sources."""
        return []

    def _build_tool_dict(self):
        self.tool_dict = {tool.name: tool for tool in self.tools}

    def get_tool_info(self, tool_name=None):
        """Get comprehensive information about tools"""
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

    def _parse_single_line_command(self, text, pattern):
        for line in text.splitlines():
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                command, arguments = match.groups()
                tool = self.tool_dict.get(command)
                if not tool:
                    return f"Unknown command: {command}"
                else:
                    return self.strip_arguments_and_execute_tool(arguments, tool)
        return ""

    def _parse_multiline_command(self, text, pattern):
        first_line = text.splitlines()[0].strip()
        match = re.match(pattern, first_line)
        if match:
            command, _ = match.groups()
            tool = self.tool_dict.get(command)
            if not tool:
                return f"Unknown command: {command}"
            else:
                if text.startswith(f"/{command} "):
                    arguments = text[len(f"/{command} "):]
                else:
                    arguments = None

                return self.strip_arguments_and_execute_tool(arguments, tool)
        return ""

    @staticmethod
    def strip_arguments_and_execute_tool(arguments, tool):
        args = arguments.strip() if arguments else None
        result = tool.execute(args)
        return result['output']

    def parse_and_execute(self, text):
        pattern = r'^/([\w-]+)(?:\s+(.*))?$'

        if '\n' in text:
            result = self._parse_multiline_command(text, pattern)
            if result:
                return result

        return self._parse_single_line_command(text, pattern)

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
                'success': result.returncode == 0,
                'output': output,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': 'Command timed out (30s limit)', 'returncode': -1}
        except Exception as e:
            return {'success': False, 'output': f'Error: {str(e)}', 'returncode': -1}
