import subprocess
from .base_tool import BaseTool

class BashTool(BaseTool):
    name = 'bash'
    description = "Execute bash commands"
    arguments = [
        {
            "name": "command",
            "type": "string",
            "required": True,
            "description": "The bash command to execute"
        }
    ]
    examples = [
        "🛠️ bash echo hello",
        "🛠️ bash ls -la",
        "🛠️ bash pwd"
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, args):
        if not args:
            return 'STDERR: bash: missing command'
        
        try:
            # Execute the command directly through bash
            result = subprocess.run(
                ['bash', '-c', args],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            
            output = result.stdout.rstrip('\n')
            
            if result.stderr:
                if output:
                    output += f"\n"
                output += f"STDERR: {result.stderr}"
            
            return output
        except subprocess.TimeoutExpired:
            return 'Command timed out (30s limit)'
        except Exception as e:
            return f'Error: {str(e)}'