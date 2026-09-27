import pytest

from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog
from tests.infrastructure.textual.widgets.tool_log_ui import ToolLogApp, ToolLogUi


@pytest.fixture
async def ui():
    app = ToolLogApp()
    async with app.run_test() as pilot:
        yield ToolLogUi(app.query_one(ToolLog), pilot)
