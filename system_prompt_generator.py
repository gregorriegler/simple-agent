#!/usr/bin/env python
from tools.tool_library import ToolLibrary

class SystemPromptGenerator:
    """Generates system prompts with dynamically discovered tools"""

    def __init__(self):
        self.tool_library = ToolLibrary()

    def generate_system_prompt(self):
        """Generate the complete system prompt with dynamic tool descriptions"""
        template_content = self._read_system_prompt_template()

        tools_content = self._generate_tools_content()

        return template_content.replace("{{DYNAMIC_TOOLS_PLACEHOLDER}}", tools_content)

    def _read_system_prompt_template(self):
        """Read the system prompt template file"""
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "system-prompt.md")

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"system-prompt.md template file not found at {template_path}")

    def _generate_tools_content(self):
        tools_lines = []

        for tool in self.tool_library.tools:
            tool_doc = self._generate_tool_documentation(tool)
            if tool_doc:
                tools_lines.append(tool_doc)

        return "\n\n".join(tools_lines)

    def _generate_tool_documentation(self, tool):
        if hasattr(tool, 'get_usage_info'):
            usage_info = tool.get_usage_info()
            return self._format_detailed_tool_doc(usage_info)
        else:
            return self._format_simple_tool_doc(tool)

    def _format_detailed_tool_doc(self, usage_info):
        lines = usage_info.split('\n')
        if not lines:
            return ""

        tool_line = lines[0]
        if not tool_line.startswith('Tool: '):
            return ""

        tool_name = tool_line.replace('Tool: ', '')

        description = ""
        for line in lines[1:]:
            if line.startswith('Description: '):
                description = line.replace('Description: ', '')
                break

        arguments = []
        in_arguments_section = False
        for line in lines:
            if line.strip() == "Arguments:":
                in_arguments_section = True
                continue
            elif in_arguments_section and line.strip().startswith("- "):
                arg = line.strip()[2:]
                arguments.append(arg)
            elif in_arguments_section and line.strip() == "":
                continue
            elif in_arguments_section and not line.strip().startswith("- ") and line.strip():
                break

        doc_lines = [f"## {tool_name}"]
        if description:
            doc_lines.append(f"{description}")
        doc_lines.append("Syntax:")

        if arguments:
            arg_syntax = " ".join([f"<{arg.split(':')[0].strip()}>" for arg in arguments])
            doc_lines.append(f"/{tool_name} {arg_syntax}")
            doc_lines.append("")
            doc_lines.append("Arguments:")
            for arg in arguments:
                doc_lines.append(f"  - {arg}")
        else:
            doc_lines.append(f"/{tool_name} {{arguments}}")

        example = self._extract_example_from_usage_info(usage_info)
        if example:
            doc_lines.append("")
            doc_lines.append("e.g.")
            doc_lines.append(example)

        return "\n".join(doc_lines)

    def _format_simple_tool_doc(self, tool):
        """Format documentation for simple static tools"""
        tool_name = tool.name
        description = getattr(tool, 'description', '')

        doc_lines = [f"## {tool_name}"]
        if description:
            doc_lines.append(description)

        doc_lines.append("Syntax:")

        if tool_name == 'ls':
            doc_lines.append("/ls {path}")
        elif tool_name == 'cat':
            doc_lines.append("/cat {path}")
        elif tool_name == 'test':
            doc_lines.append("/test {directory}")
        elif tool_name == 'revert':
            doc_lines.append("/revert {directory}")
        else:
            doc_lines.append(f"/{tool_name} {{arguments}}")

        return "\n".join(doc_lines)

    def _extract_example_from_usage_info(self, usage_info):
        """Extract example from usage info if available"""
        lines = usage_info.split('\n')
        for i, line in enumerate(lines):
            if 'example' in line.lower() or 'e.g.' in line.lower():
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        return lines[j].strip()
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate system prompt with dynamic tool descriptions',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: stdout)',
        default=None
    )

    args = parser.parse_args()

    generator = SystemPromptGenerator()
    system_prompt = generator.generate_system_prompt()

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(system_prompt)
        print(f"System prompt written to {args.output}")
    else:
        print(system_prompt)


if __name__ == "__main__":
    main()
