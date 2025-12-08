import os
import unittest
from approvaltests import verify
from simple_agent.tools.replace_content_tool import ReplaceContentTool
from simple_agent.application.tool_library import RawToolCall

class ReplaceContentToolTest(unittest.TestCase):
    def test_replace_content_success(self):
        # Create a dummy file
        with open("test.txt", "w") as f:
            f.write("Hello, world!\\nThis is a test file.\\n")

        tool = ReplaceContentTool()
        raw_call = RawToolCall(
            name="replace-content",
            arguments="test.txt",
            body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
        )
        result = tool.execute(raw_call)

        with open("test.txt", "r") as f:
            content = f.read()

        os.remove("test.txt")

        self.assertTrue(result.success)
        self.assertEqual("Hello, universe!\\nThis is a test file.\\n", content)
        verify(result.message)

    def test_replace_content_file_not_found(self):
        tool = ReplaceContentTool()
        raw_call = RawToolCall(
            name="replace-content",
            arguments="nonexistent.txt",
            body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
        )
        result = tool.execute(raw_call)

        self.assertFalse(result.success)
        verify(result.message)

    def test_replace_content_search_content_not_found(self):
        # Create a dummy file
        with open("test.txt", "w") as f:
            f.write("This is a test file.\\n")

        tool = ReplaceContentTool()
        raw_call = RawToolCall(
            name="replace-content",
            arguments="test.txt",
            body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
        )
        result = tool.execute(raw_call)

        os.remove("test.txt")

        self.assertFalse(result.success)
        verify(result.message)

    def test_replace_content_invalid_format(self):
        tool = ReplaceContentTool()
        raw_call = RawToolCall(
            name="replace-content",
            arguments="test.txt",
            body="""< SEARCH
Hello, world!
---
Hello, universe!
> REPLACE
"""
        )
        result = tool.execute(raw_call)

        self.assertFalse(result.success)
        verify(result.message)

    def test_replace_content_empty_search_block(self):
        tool = ReplaceContentTool()
        raw_call = RawToolCall(
            name="replace-content",
            arguments="test.txt",
            body="""<<<<<<< SEARCH
=======
Hello, universe!
>>>>>>> REPLACE
"""
        )
        result = tool.execute(raw_call)

        self.assertFalse(result.success)
        verify(result.message)

    def test_replace_content_replaces_only_first_occurrence(self):
        # Create a dummy file
        with open("test.txt", "w") as f:
            f.write("Hello, world!\\nHello, world!\\n")

        tool = ReplaceContentTool()
        raw_call = RawToolCall(
            name="replace-content",
            arguments="test.txt",
            body="""<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
"""
        )
        result = tool.execute(raw_call)

        with open("test.txt", "r") as f:
            content = f.read()

        os.remove("test.txt")

        self.assertTrue(result.success)
        self.assertEqual("Hello, universe!\\nHello, world!\\n", content)
        verify(result.message)
