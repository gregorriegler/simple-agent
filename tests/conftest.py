"""Global pytest configuration for all tests."""
import os

import pytest
from approvaltests import set_default_reporter
from approvaltests.reporters import ReportWithWinMerge

from .custom_reporter import ApproveShReporter


@pytest.fixture(scope="session", autouse=True)
def configure_approvals():
    use_approve_sh_reporter = os.getenv("USE_APPROVE_SH_REPORTER", 'False').lower() in ('true', '1', 't')
    if use_approve_sh_reporter:
        set_default_reporter(ApproveShReporter())
    else:
        set_default_reporter(ReportWithWinMerge())

