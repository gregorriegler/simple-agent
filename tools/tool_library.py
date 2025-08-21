import re
import subprocess

from .ls_tool import LsTool
from .cat_tool import CatTool
from .test_tool import TestTool
from .mutation_tool import MutationTool
from .revert_tool import RevertTool
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
            LsTool(self.runcommand),
            CatTool(self.runcommand),
            TestTool(self.runcommand),
            MutationTool(self.runcommand),
            RevertTool(self.runcommand),
            CreateFileTool(self.runcommand),
            EditFileTool(self.runcommand)
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


    def _parse_multiline_command(self, text, pattern):
        """Handle multi-line commands by treating the entire text as one command"""
        first_line = text.splitlines()[0].strip()
        match = re.match(pattern, first_line)
        if match:
            command, _ = match.groups()
            tool = self.tool_dict.get(command)
            if tool:
                # Extract arguments from the entire text, preserving newlines
                # Find the position after "/{command} " in the text
                command_prefix = f"/{command} "
                if text.startswith(command_prefix):
                    full_args = text[len(command_prefix):]
                    result = tool.execute(full_args.strip() if full_args else None)
                    return text, result['output']
                else:
                    result = tool.execute(None)
                    return text, result['output']
            else:
                return text, f"Unknown command: {command}"
        return None

    def _parse_single_line_command(self, text, pattern):
        """Handle single-line command processing"""
        for line in text.splitlines():
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                command, arguments = match.groups()
                tool = self.tool_dict.get(command)
                if tool:
                    result = tool.execute(arguments.strip() if arguments else None)
                    return line, result['output']
                else:
                    return line, f"Unknown command: {command}"
        return text.splitlines()[0].strip(), ""

    def parse_and_execute(self, text):
        pattern = r'^/([\w-]+)(?:\s+(.*))?$'

        # Handle multi-line commands by treating the entire text as one command
        if '\n' in text:
            result = self._parse_multiline_command(text, pattern)
            if result:
                return result

        # Single-line processing (original behavior)
        return self._parse_single_line_command(text, pattern)

    def runcommand(self, command, args=None, cwd=None):
        try:
            if args:
                if isinstance(args, str):
                    args = [args]
                command_line = [command] + args
            else:
                command_line = [command]

            timeout = 300 if (args and 'stryker' in args) else 30

            result = subprocess.run(
                command_line,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                cwd=cwd
            )

            output = result.stdout.rstrip('\n')

            if result.stderr:
                stderr = result.stderr
                if output:  # Only add newline if there's stdout content
                    output += f"\nSTDERR: {stderr}"
                else:
                    output = f"STDERR: {stderr}"

            return {
                'success': result.returncode == 0,
                'output': output,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': 'Command timed out (30s limit)', 'returncode': -1}
        except Exception as e:
            return {'success': False, 'output': f'Error: {str(e)}', 'returncode': -1}
