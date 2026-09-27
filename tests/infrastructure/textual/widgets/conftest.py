import pytest

from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog
from tests.infrastructure.textual.widgets.agent_tabs_ui import AgentTabsApp, AgentTabsUi
from tests.infrastructure.textual.widgets.tool_log_ui import ToolLogApp, ToolLogUi


@pytest.fixture
async def ui():
    app = ToolLogApp()
    async with app.run_test() as pilot:
        yield ToolLogUi(app.query_one(ToolLog), pilot)


@pytest.fixture
async def tabs():
    app = AgentTabsApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        yield AgentTabsUi(app.query_one(AgentTabs), pilot)
