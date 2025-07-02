"""Global pytest configuration for all tests."""
import pytest
from approvaltests import set_default_reporter
from approvaltests.reporters.python_native_reporter import PythonNativeReporter


@pytest.fixture(scope="session", autouse=True)
def configure_approvals():
    """Configure approvals testing for all test files."""
    set_default_reporter(PythonNativeReporter())