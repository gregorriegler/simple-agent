import os
import re
import subprocess


class ToolFramework:
    def __init__(self):
        self.tools = {
            'ls': self._ls,
            'cat': self._cat,
            'test': self._test,
            'extract-method': self._extract_method,
            'inline-method': self._inline_method,
            'revert': self._revert,
        }
        
    def parse_and_execute(self, text):
        pattern = r'^/([\w-]+)(?:\s+(.*))?$'
        for line in text.splitlines():
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                cmd, arg = match.groups()
                tool_fn = self.tools.get(cmd)
                if tool_fn:
                    result = tool_fn(arg.strip() if arg else None)
                    return f"{line}\n{result['output']}", result['output']
                else:
                    return f"{line}\nUnknown command: {cmd}", f"Unknown command: {cmd}"
        return text.splitlines()[0].strip(), ""


    def _ls(self, path='.'):
        return self.runcommand('ls', ['-la', path] if path else ['-la'])

    def _cat(self, filename):
        return self.runcommand('cat', ['-n', filename])

    def _test(self, path):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.sh')
        return self.runcommand('bash', [script_path, path])
        
    def _extract_method(self, args):
        arg_list = args.split()
        return self.runcommand('dotnet', ['run', '--', 'extract-method'] + arg_list, cwd='ExtractMethodTool')

    def _inline_method(self, args):
        arg_list = args.split()
        return self.runcommand('dotnet', ['run', '--', 'inline-method'] + arg_list, cwd='ExtractMethodTool')
        
    def _revert(self, directory='.'):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'revert.sh')
        return self.runcommand('bash', [script_path, directory])

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

