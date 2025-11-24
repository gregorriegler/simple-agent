import subprocess
from simple_agent.application.tool_library import ToolResult, Tool


class BaseTool(Tool):
    name = ''
    description = ''
    arguments = []
    examples = []
    _custom_usage_info = None

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

    def get_usage_info(self):
        if hasattr(self, '_custom_usage_info') and self._custom_usage_info is not None:
            return self._custom_usage_info()

        return self._generate_usage_info_from_metadata()

    def finalize_documentation(self, doc: str, context: dict) -> str:
        return doc

    def _generate_usage_info_from_metadata(self):
        lines = [f"Tool: {self.name}"]

        if self.description:
            lines.append(f"Description: {self.description}")

        if self.arguments:
            lines.append("")
            lines.append("Arguments:")
            for arg in self.arguments:
                required_str = " (required)" if arg.get('required', False) else " (optional)"
                type_str = f" - {arg['name']}: {arg.get('type', 'string')}{required_str}"
                if 'description' in arg:
                    type_str += f" - {arg['description']}"
                lines.append(type_str)

            # Generate syntax
            lines.append("")
            required_args = [f"<{arg['name']}>" for arg in self.arguments if arg.get('required', False)]
            optional_args = [f"[{arg['name']}]" for arg in self.arguments if not arg.get('required', False)]
            all_args = required_args + optional_args
            syntax = f"🛠️ {self.name}"
            if all_args:
                syntax += " " + " ".join(all_args)
            lines.append(f"Usage: {syntax}")

        if hasattr(self, 'examples') and self.examples:
            lines.append("")
            lines.append("Examples:")
            for example in self.examples:
                lines.append(f"{example}")

        return "\n".join(lines)
