import re
import subprocess


class ToolFramework:
    def __init__(self):
        self.tools = {
            'ls': self._ls,
            'cat': self._cat,
            'extract-method': self._extract_method,
            'inline-method': self._inline_method,
        }

    def runcommand(self, cmd, args=None, cwd=None):
        try:
            if args:
                if isinstance(args, str):
                    args = [args]
                command_line = [cmd] + args
            else:
                command_line = [cmd]
    
            # Show the exact command being run, including cwd
            cmd_str = ' '.join(command_line)
            if cwd:
                print(f"[cwd: {cwd}] $ {cmd_str}")
            else:
                print(f"$ {cmd_str}")
    
            result = subprocess.run(command_line, capture_output=True, text=True, timeout=30, cwd=cwd)
    
            output = result.stdout
            print(output)
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


    def _run_command(self, cmd, args=None, cwd=None):
        return self.runcommand(cmd, args, cwd=cwd)

    def _ls(self, path='.'):
        return self._run_command('ls', ['-la', path] if path else ['-la'])

    def _cat(self, filename):
        return self._run_command('cat', ['-n', filename])
        
    def _extract_method(self, args):
        arg_list = args.split()
        return self._run_command('dotnet', ['run', '--', 'extract-method'] + arg_list, cwd='ExtractMethodTool')

    def _inline_method(self, args):
        arg_list = args.split()
        return self._run_command('dotnet', ['run', '--', 'inline-method'] + arg_list, cwd='ExtractMethodTool')


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
