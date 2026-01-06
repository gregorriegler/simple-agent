"""Global pytest configuration for all tests."""

import os
import sys

import pytest
from approvaltests import set_default_reporter
from approvaltests.reporters import ReportWithWinMerge

from .approve_sh_reporter import ApproveShReporter


@pytest.fixture(scope="session", autouse=True)
def configure_approvals():
    # Fix Unicode encoding issues on Windows
    if sys.platform == "win32":
        from approvaltests.string_writer import StringWriter

        # Monkey-patch the write_received_file method to use UTF-8 encoding
        def utf8_write_received_file(self, received_file):
            """Write the received file using UTF-8 encoding with normalized line endings."""
            # Normalize line endings to LF to match .gitattributes and .editorconfig
            content = self.contents.replace("\r\n", "\n").replace("\r", "\n")
            with open(received_file, "w", encoding="utf-8", newline="\n") as file:
                file.write(content)
            return received_file

        StringWriter.write_received_file = utf8_write_received_file

    use_approve_sh_reporter = os.getenv("USE_APPROVE_SH_REPORTER", "False").lower() in (
        "true",
        "1",
        "t",
    )
    if use_approve_sh_reporter:
        set_default_reporter(ApproveShReporter())
    else:
        set_default_reporter(ReportWithWinMerge())
