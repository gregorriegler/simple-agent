import textwrap
from pathlib import Path

from approvaltests import Options, verify
from simple_agent.tools.all_tools import AllTools
from .test_helpers import all_scrubbers, temp_directory

library = AllTools()


def test_write_todos_creates_markdown_file(tmp_path):
    command = textwrap.dedent("""
    🛠️ write-todos
    - [ ] Item 1
    - [ ] **Work in progress**
    - [x] Completed
    🛠️🔚
    """).strip()

    with temp_directory(tmp_path):
        tool = library.parse_message_and_tools(command)
        result = library.execute_parsed_tool(tool.tools[0])

        content = Path(".Agent.todos.md").read_text(encoding="utf-8")
        verify(
            f"Command:\n{command}\n\nResult:\n{result}\n\nFile content:\n--- FILE CONTENT START ---\n{content}\n--- FILE CONTENT END ---",
            options=Options().with_scrubber(all_scrubbers())
        )
