import pytest
import textwrap
from pathlib import Path

from approvaltests import Options, verify
from tests.test_helpers import all_scrubbers, temp_directory, create_all_tools_for_test

library = create_all_tools_for_test()
pytestmark = pytest.mark.asyncio


async def test_write_todos_creates_markdown_file(tmp_path):
    command = textwrap.dedent("""
    🛠️[write-todos]
    - [ ] Item 1
    - [ ] **Work in progress**
    - [x] Completed
    🛠️[/end]
    """).strip()

    with temp_directory(tmp_path):
        tool = library.parse_message_and_tools(command)
        result = await library.execute_parsed_tool(tool.tools[0])

        content = Path(".Agent.todos.md").read_text(encoding="utf-8")
        verify(
            f"Command:\n{command}\n\nResult:\n{result}\n\nFile content:\n--- FILE CONTENT START ---\n{content}\n--- FILE CONTENT END ---",
            options=Options().with_scrubber(all_scrubbers())
        )
