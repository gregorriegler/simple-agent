from textual.app import App, ComposeResult
from textual.widgets import TabPane

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import AgentFinishedEvent, AgentStartedEvent
from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs
from simple_agent.tools.all_tools import TOOL_DECLARATIONS

ROOT = "Agent"


class AgentTabsApp(App):
    def compose(self) -> ComposeResult:
        yield AgentTabs(None, AgentId(ROOT), TOOL_DECLARATIONS)


class AgentTabsUi:
    def __init__(self, tabs: AgentTabs, pilot):
        self._tabs = tabs
        self._pilot = pilot

    async def start(self, agent: str) -> None:
        self._tabs.handle_event(AgentStartedEvent(AgentId(agent), agent, ""))
        await self._pilot.pause()

    async def focus(self, agent: str) -> None:
        self._tabs.activate_tab(AgentId(agent))
        await self._pilot.pause()

    async def finish(self, agent: str) -> None:
        self._tabs.handle_event(AgentFinishedEvent(AgentId(agent)))
        await self._pilot.pause()

    def outline(self) -> str:
        return "\n".join(
            f"{'>' if pane.id == self._tabs.active else ' '} {pane.id}"
            for pane in self._tabs.query(TabPane)
        )
