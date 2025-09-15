#!/usr/bin/env python
from tools.tool_library import ToolLibrary

class SystemPromptGenerator:

    def __init__(self):
        self.tool_library = ToolLibrary()

    def generate_system_prompt(self):
        template_content = self._read_system_prompt_template()
        agents_content = self._read_agents_content()
        tools_content = self._generate_tools_content()
        
        # Replace the dynamic tools placeholder
        result = template_content.replace("{{DYNAMIC_TOOLS_PLACEHOLDER}}", tools_content)
        
        # Add agents content at the beginning
        return agents_content + "\n\n" + result

    def _read_system_prompt_template(self):
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "system-prompt.md")

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"system-prompt.md template file not found at {template_path}")

    def _read_agents_content(self):
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        agents_path = os.path.join(script_dir, "AGENTS.md")
        
        try:
            with open(agents_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # If AGENTS.md doesn't exist, return empty string to avoid breaking
            return ""

    def _generate_tools_content(self):
        tools_lines = []

        for tool in self.tool_library.tools:
            tool_doc = self._generate_tool_documentation(tool)
            tools_lines.append(tool_doc)

        return "\n\n".join(tools_lines)

    def _generate_tool_documentation(self, tool):
        usage_info = tool.get_usage_info()
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

        # Simply return the full usage_info after the tool name and description
        remaining_lines = usage_info.split('\n')[2:]  # Skip "Tool: name" and "Description: ..." lines
        if remaining_lines:
            doc_lines.extend(remaining_lines)

        return "\n".join(doc_lines)


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

