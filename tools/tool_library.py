import re
import subprocess

from .ls_tool import LsTool
from .cat_tool import CatTool
from .create_file_tool import CreateFileTool
from .edit_file_tool import EditFileTool
from .subagent_tool import SubagentTool


class ParsedTool:
    """Represents a parsed tool with its name, arguments, and tool instance."""
    def __init__(self, name, arguments, tool_instance):
        self.name = name
        self.arguments = arguments
        self.tool_instance = tool_instance

    def __str__(self):
        args_str = f" {self.arguments}" if self.arguments else ""
        return f"Tool: {self.name}{args_str}"


class ToolLibrary:
    def __init__(self, message_claude = lambda messages, system_prompt: ""):
        self.message_claude = message_claude
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
            EditFileTool(self.run_command),
            SubagentTool(self.run_command, self.message_claude)
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

    def parse_tool(self, text):
        pattern = r'^/([\w-]+)(?:\s+(.*))?$'

        if '\n' in text:
            return self._parse_multiline_command(text, pattern)

        return self._parse_single_line_command(text, pattern)

    def _parse_single_line_command(self, text, pattern):
        for line in text.splitlines():
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                command, arguments = match.groups()
                tool = self.tool_dict.get(command)
                if not tool:
                    return None, f"Unknown command: {command}"
                else:
                    return ParsedTool(command, arguments, tool)
        return None

    def _parse_multiline_command(self, text, pattern):
        first_line = text.splitlines()[0].strip()
        match = re.match(pattern, first_line)
        if match:
            command, _ = match.groups()
            tool = self.tool_dict.get(command)
            if not tool:
                return None, f"Unknown command: {command}"
            else:
                if text.startswith(f"/{command} "):
                    arguments = text[len(f"/{command} "):]
                else:
                    arguments = None

                return ParsedTool(command, arguments, tool)
        return None

    def execute_parsed_tool(self, parsed_tool):
        args = parsed_tool.arguments.strip() if parsed_tool.arguments else None
        result = parsed_tool.tool_instance.execute(args)
        return result['output']

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
