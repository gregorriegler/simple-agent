import subprocess
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Dict, Iterable, List

from simple_agent.application.tool_library import ToolResult, Tool, ToolArgument


class BaseTool(Tool):
    name = ''
    description = ''
    arguments: List[ToolArgument] = []
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

    def _normalize_argument(self, arg: ToolArgument | Dict[str, Any]) -> Dict[str, Any]:
        if is_dataclass(arg):
            normalized = asdict(arg)
        else:
            normalized = dict(arg)

        normalized.setdefault("type", "string")
        normalized.setdefault("required", False)
        normalized.setdefault("description", "")
        normalized.setdefault("multiline", False)
        return normalized

    def _format_example(self, example: Any, arguments: Iterable[Dict[str, Any]]):
        if isinstance(example, str):
            return example

        if not isinstance(example, dict):
            return str(example)

        inline_values = []
        multiline_values = []

        for arg in arguments:
            value = example.get(arg["name"], "")
            if value is None:
                value = ""

            if arg.get("multiline"):
                if value != "":
                    multiline_values.append(str(value))
            else:
                if value != "":
                    inline_values.append(str(value))

        syntax = f"🛠️ {self.name}"
        if inline_values:
            syntax += " " + " ".join(inline_values)

        if multiline_values:
            multiline_text = "\n".join(multiline_values)
            syntax += "\n" + multiline_text
            if multiline_text.endswith("\n"):
                syntax += "🛠️🔚"
            elif "\n" in multiline_text:
                syntax += "\n🛠️🔚"
            else:
                syntax += "🛠️🔚"

        return syntax

    def _generate_usage_info_from_metadata(self):
        lines = [f"Tool: {self.name}"]

        if self.description:
            lines.append(f"Description: {self.description}")

        if self.arguments:
            lines.append("")
            lines.append("Arguments:")
            normalized_args = [self._normalize_argument(arg) for arg in self.arguments]
            for arg in normalized_args:
                required_str = " (required)" if arg.get('required', False) else " (optional)"
                type_str = f" - {arg['name']}: {arg.get('type', 'string')}{required_str}"
                if 'description' in arg:
                    type_str += f" - {arg['description']}"
                lines.append(type_str)

            # Generate syntax
            lines.append("")
            required_args = [f"<{arg['name']}>" for arg in normalized_args if arg.get('required', False)]
            optional_args = [f"[{arg['name']}]" for arg in normalized_args if not arg.get('required', False)]
            all_args = required_args + optional_args
            syntax = f"🛠️ {self.name}"
            if all_args:
                syntax += " " + " ".join(all_args)
            lines.append(f"Usage: {syntax}")

        if hasattr(self, 'examples') and self.examples:
            lines.append("")
            lines.append("Examples:")
            example_args = [self._normalize_argument(arg) for arg in self.arguments]
            for example in self.examples:
                lines.append(self._format_example(example, example_args))

        return "\n".join(lines)
