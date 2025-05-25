import subprocess
import re
from pathlib import Path

class ToolFramework:
    def __init__(self):
        self.tools = {
            'ls': self._ls,
            'cat': self._cat,
        }

    def runcommand(self, cmd, args=None):
        """Safely run a command and return result."""
        try:
            if args:
                if isinstance(args, str):
                    args = [args]
                result = subprocess.run([cmd] + args, capture_output=True, text=True, timeout=30)
            else:
                result = subprocess.run([cmd], capture_output=True, text=True, timeout=30)

            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"

            return {
                'success': result.returncode == 0,
                'output': output.strip(),
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': 'Command timed out (30s limit)', 'returncode': -1}
        except Exception as e:
            return {'success': False, 'output': f'Error: {str(e)}', 'returncode': -1}

    def _run_command(self, cmd, args=None):
        return self.runcommand(cmd, args)

    def _ls(self, path='.'):
        """List directory contents."""
        return self._run_command('ls', ['-la', path] if path else ['-la'])

    def _cat(self, filename):
        """Display file contents."""
        return self._run_command('cat', [filename])

    def parse_and_execute(self, text):
        """Parse text for tool invocations and execute them."""
        # Match any registered tool: e.g., /toolname [optional args...]
        pattern = r'^/(\w+)(?:\s+(.*))?$'
        lines = text.splitlines()
        full_output = []
        result_output = []

        for line in lines:
            match = re.match(pattern, line.strip())
            if match:
                cmd, arg = match.groups()
                tool_fn = self.tools.get(cmd)
                if tool_fn:
                    result = tool_fn(arg.strip() if arg else None)
                    command_output = result['output']
                    full_output.append(f"{line}\n{command_output}")
                    result_output.append(command_output)
                else:
                    full_output.append(f"{line}\nUnknown command: {cmd}")
                    result_output.append(f"Unknown command: {cmd}")
            else:
                full_output.append(line)

        return "\n".join(full_output), "\n".join(result_output)
