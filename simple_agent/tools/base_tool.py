import subprocess
from typing import List

from simple_agent.application.tool_library import ToolResult, Tool, ToolArgument
from simple_agent.application.emoji_tool_syntax import EmojiToolSyntax

CURRENT_SYNTAX = EmojiToolSyntax()


class BaseTool(Tool):
    name = ''
    description = ''
    arguments: List[ToolArgument] = []
    examples = []

    def execute(self, *args, **kwargs) -> ToolResult:
        raise NotImplementedError("Subclasses must implement execute()")

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
                'output': output,
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {'output': 'Command timed out (30s limit)', 'success': False}
        except Exception as e:
            return {'output': f'Error: {str(e)}', 'success': False}

    def finalize_documentation(self, doc: str, context: dict) -> str:
        return doc
