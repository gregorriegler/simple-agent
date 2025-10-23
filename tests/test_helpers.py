import os
from contextlib import contextmanager

from approvaltests import Options, verify
from approvaltests.scrubbers.scrubbers import create_regex_scrubber, combine_scrubbers

from simple_agent.application.input import Input
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.console.console_subagent_display import ConsoleSubagentDisplay
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.tools.all_tools import AllTools


def create_all_tools_for_test():
    from simple_agent.application.agent_factory import AgentFactory
    from simple_agent.application.event_bus import SimpleEventBus
    from simple_agent.infrastructure.system_prompt.agent_definition import (
        load_agent_prompt
    )
    from simple_agent.tools.subagent_context import SubagentContext

    io = StdIO()
    create_subagent_display = lambda agent_id, indent: ConsoleSubagentDisplay(indent, agent_id, io, None)
    create_subagent_input = lambda indent: Input(ConsoleUserInput(indent, io))

    from simple_agent.application.session_storage import NoOpSessionStorage
    event_bus = SimpleEventBus()
    llm = lambda system_prompt, messages: ''
    create_agent = AgentFactory(
        llm,
        event_bus,
        create_subagent_display,
        create_subagent_input,
        load_agent_prompt,
        NoOpSessionStorage()
    )

    subagent_context = SubagentContext(
        create_agent,
        create_subagent_display,
        create_subagent_input,
        0,
        "Agent"
    )

    return AllTools(subagent_context)


def create_temp_file(tmp_path, filename, contents):
    temp_file = tmp_path / filename
    temp_file.write_text(contents)
    return temp_file


@contextmanager
def temp_directory(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield
    finally:
        os.chdir(original_cwd)


def create_temp_directory_structure(tmp_path):
    file1 = tmp_path / "file1.txt"
    file1.write_text("Hello world\nLine 2\nLine 3")

    file2 = tmp_path / "file2.py"
    file2.write_text("def hello():\n    print('Hello')\n    return 42")

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subfile = subdir / "subfile.txt"
    subfile.write_text("Subdirectory file content")

    return tmp_path, file1, file2, subdir, subfile


def create_path_scrubber():
    def path_replacer(text):
        lines = text.split('\n')
        result_lines = []

        for line in lines:
            new_line = scrub_line_with_path(line)
            result_lines.append(new_line)

        return '\n'.join(result_lines)

    return path_replacer


def scrub_line_with_path(line):
    import re

    def replace_path(match):
        path = match.group(0)

        if re.match(r'^/[a-z-]+$', path):
            return path

        if re.search(r'\.[A-Za-z0-9]+$', path):
            filename = os.path.basename(path)
            return f'/tmp/test_path/{filename}'
        else:
            return '/tmp/test_path'

    windows_pattern = r'[A-Za-z]:[/\\](?:[^<>:"|?*\n\r]+[/\\])*[^<>:"|?*\n\r\s]*(?:\.[A-Za-z0-9]+)?'
    result = re.sub(windows_pattern, replace_path, line)

    unix_pattern = r"'(/(?:[^/\s<>:\"|?*\n\r]+/)*[^/\s<>:\"|?*\n\r]*)'|(/(?:[^/\s<>:\"|?*\n\r]+/)+[^/\s<>:\"|?*\n\r]*)|(/[^/\s<>:\"|?*\n\r]*\.[A-Za-z0-9]+)"

    def replace_unix_path(match):
        if match.group(1):
            path = match.group(1)

            class MockMatch:
                def group(self, n):
                    return path
            replaced = replace_path(MockMatch())
            return f"'{replaced}'"
        elif match.group(2):
            return replace_path(match)
        elif match.group(3):
            return replace_path(match)
        return match.group(0)

    result = re.sub(unix_pattern, replace_unix_path, result)

    return result


def create_date_scrubber():
    return create_regex_scrubber(
        r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}',
        '[DATE]'
    )


def create_ls_error_scrubber():
    """Normalize ls error messages between Mac and Linux"""

    def ls_error_replacer(text):
        import re
        if "cannot access" not in text:
            pattern = r"ls: ([^:]+): No such file or directory"
            replacement = r"ls: cannot access '\1': No such file or directory"
            return re.sub(pattern, replacement, text)
        return text

    return ls_error_replacer


def all_scrubbers():
    return combine_scrubbers(
        create_path_scrubber(),
        create_date_scrubber(),
        create_ls_error_scrubber()
    )


def verify_tool(library, command):
    tool = library.parse_message_and_tools(command)
    result = library.execute_parsed_tool(tool.tools[0])
    verify(f"Command:\n{command}\n\nResult:\n{result}", options=Options()
           .with_scrubber(all_scrubbers()))
