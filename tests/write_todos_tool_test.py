from pathlib import Path

from approvaltests import Options, verify
from simple_agent.tools.tool_library import AllTools
from .test_helpers import all_scrubbers, temp_directory

library = AllTools()


def test_write_todos_creates_markdown_file(tmp_path):
    command = "🛠️ write-todos ## Todo\n- Item 1\n\n## Doing\n- Work in progress\n\n## Done\n- Completed"

    with temp_directory(tmp_path):
        tool = library.parse_tool(command)
        result = library.execute_parsed_tool(tool)

        content = Path(".Agent.todos.md").read_text(encoding="utf-8")
        verify(
            f"Command:\n{command}\n\nResult:\n{result}\n\nFile content:\n--- FILE CONTENT START ---\n{content}\n--- FILE CONTENT END ---",
            options=Options().with_scrubber(all_scrubbers())
        )
