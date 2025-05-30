import re
import subprocess

from .ls_tool import LsTool
from .cat_tool import CatTool
from .test_tool import TestTool
from .extract_method_tool import ExtractMethodTool
from .inline_method_tool import InlineMethodTool
from .revert_tool import RevertTool

class ToolLibrary:
    def __init__(self):
        self.tools = [
            LsTool(self.runcommand),
            CatTool(self.runcommand),
            TestTool(self.runcommand),
            ExtractMethodTool(self.runcommand),
            InlineMethodTool(self.runcommand),
            RevertTool(self.runcommand)
        ]
        self._build_tool_dict()
    
    def _build_tool_dict(self):
        self.tool_dict = {tool.name: tool for tool in self.tools}
        
    def parse_and_execute(self, text):
        pattern = r'^/([\w-]+)(?:\s+(.*))?$'
        for line in text.splitlines():
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                cmd, arg = match.groups()
                tool = self.tool_dict.get(cmd)
                if tool:
                    result = tool.execute(arg.strip() if arg else None)
                    return f"{line}\n{result['output']}", result['output']
                else:
                    return f"{line}\nUnknown command: {cmd}", f"Unknown command: {cmd}"
        return text.splitlines()[0].strip(), ""

    def runcommand(self, cmd, args=None, cwd=None):
        try:
            if args:
                if isinstance(args, str):
                    args = [args]
                command_line = [cmd] + args
    
            result = subprocess.run(
                command_line,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30,
                cwd=cwd
            )
    
            output = result.stdout
            print(output, end='')
            if result.stderr:
                stderr = result.stderr
                print(f"\nSTDERR: {stderr}", end='')
                output += f"\nSTDERR: {stderr}"
    
            return {
                'success': result.returncode == 0,
                'output': output.strip(),
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': 'Command timed out (30s limit)', 'returncode': -1}
        except Exception as e:
            return {'success': False, 'output': f'Error: {str(e)}', 'returncode': -1}

