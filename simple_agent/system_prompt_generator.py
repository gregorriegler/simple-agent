#!/usr/bin/env python
import os
import glob
from simple_agent.application.tool_library import ToolLibrary

def discover_agent_types() -> list[str]:
    simple_agent_dir = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(simple_agent_dir, '*.agent.md')
    agent_files = glob.glob(pattern)
    agent_types = []
    for filepath in agent_files:
        basename = os.path.basename(filepath)
        agent_type = basename.replace('.agent.md', '')
        agent_types.append(agent_type)
    return sorted(agent_types)

def extract_tool_keys_from_file(filename: str) -> list[str]:
    try:
        from importlib import resources
        content = resources.read_text('simple_agent', filename)
    except FileNotFoundError:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

    return extract_tool_keys_from_prompt(content)

def extract_tool_keys_from_prompt(system_prompt_md: str) -> list[str]:
    separator = "---"
    if separator not in system_prompt_md:
        return []

    top_section = system_prompt_md.split(separator, 1)[0].strip()
    if not top_section:
        return []

    lines = top_section.split('\n')
    first_line = lines[0].strip()

    if ',' in first_line:
        tool_keys = [key.strip() for key in first_line.split(',') if key.strip()]
        return tool_keys if tool_keys else []

    return []

def generate_system_prompt(system_prompt_md: str, tool_library: ToolLibrary):
    template_content = _read_system_prompt_template(system_prompt_md)
    agents_content = _read_agents_content()
    tools_content = generate_tools_content(tool_library)

    # Replace the dynamic tools placeholder
    result = template_content.replace("{{DYNAMIC_TOOLS_PLACEHOLDER}}", tools_content)

    # Add agents content at the end
    return result + "\n\n" + agents_content



def _read_system_prompt_template(system_prompt_md):
        try:
            from importlib import resources
            content = resources.read_text('simple_agent', '%s' % system_prompt_md)
        except FileNotFoundError:
            import os
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_path = os.path.join(script_dir, "%s" % system_prompt_md)

            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"%s template file not found at {template_path}" % system_prompt_md)

        return _strip_tool_keys_section(content)


def _strip_tool_keys_section(content: str) -> str:
    separator = "---"
    if separator not in content:
        return content

    parts = content.split(separator, 1)
    if len(parts) < 2:
        return content

    content = "---".join(parts[1:])
    return content


def _read_agents_content():
        import os
        # Look for AGENTS.md in the current working directory
        agents_path = os.path.join(os.getcwd(), "AGENTS.md")

        try:
            # Try UTF-8 first, then fall back to other encodings
            try:
                with open(agents_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # Try with UTF-8 and error handling
                with open(agents_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
        except FileNotFoundError:
            # If AGENTS.md doesn't exist, return empty string to avoid breaking
            return ""

def generate_tools_content(tool_library: ToolLibrary):
    tools_lines = []

    for tool in tool_library.tools:
        tool_doc = _generate_tool_documentation(tool)
        tools_lines.append(tool_doc)

    return "\n\n".join(tools_lines)


def _generate_tool_documentation(tool):
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

        remaining_lines = usage_info.split('\n')[2:]

        if tool_name == 'subagent':
            agent_types = discover_agent_types()
            if agent_types:
                agent_types_list = ', '.join(f"'{t}'" for t in agent_types)
                injected_lines = []
                for line in remaining_lines:
                    if 'agenttype:' in line.lower() and '{{AGENT_TYPES}}' in line:
                        injected_lines.append(f" - agenttype: string (required) - Type of agent to create. Available types: {agent_types_list}")
                    else:
                        injected_lines.append(line)
                remaining_lines = injected_lines

        if remaining_lines:
            doc_lines.extend(remaining_lines)

        return "\n".join(doc_lines)


def main():
    import argparse
    from simple_agent.tools.all_tools import AllTools

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

    from simple_agent.application.input import Input
    from simple_agent.application.user_input import UserInput

    class DummyUserInput(UserInput):
        def read(self):
            return ""
        def escape_requested(self):
            return False

    def dummy_display(agent_id, indent_level):
        pass

    def dummy_input(indent_level):
        return Input(DummyUserInput())

    tool_library = AllTools(
        create_subagent_display=dummy_display,
        create_subagent_input=dummy_input
    )
    system_prompt = generate_system_prompt('default.agent.md', tool_library)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(system_prompt)
        print(f"System prompt written to {args.output}")
    else:
        print(system_prompt)


if __name__ == "__main__":
    main()

