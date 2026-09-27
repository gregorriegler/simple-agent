from textual.app import App, ComposeResult
from textual.widgets import Markdown, TabPane

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantSaidEvent,
    SessionClearedEvent,
)
from simple_agent.application.on_complete import OnComplete
from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs
from simple_agent.infrastructure.textual.widgets.chat_log import ChatLog
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
        self._tabs.handle_event(
            AgentStartedEvent(AgentId(agent), agent, on_complete=OnComplete.CLOSE)
        )
        await self._pilot.pause()

    async def focus(self, agent: str) -> None:
        self._tabs.activate_tab(AgentId(agent))
        await self._pilot.pause()

    async def finish(self, agent: str) -> None:
        self._tabs.handle_event(AgentFinishedEvent(AgentId(agent)))
        await self._pilot.pause()

    async def say(self, agent: str, message: str) -> None:
        self._tabs.handle_event(AssistantSaidEvent(AgentId(agent), message))
        await self._pilot.pause()

    async def clear(self, agent: str) -> None:
        self._tabs.handle_event(SessionClearedEvent(AgentId(agent)))
        await self._pilot.pause()

    async def next_tab(self) -> None:
        self._tabs.switch_tab(1)
        await self._pilot.pause()

    async def previous_tab(self) -> None:
        self._tabs.switch_tab(-1)
        await self._pilot.pause()

    def outline(self) -> str:
        return "\n".join(
            _outline(pane, self._tabs.active) for pane in self._tabs.query(TabPane)
        )


def _outline(pane: TabPane, active: str) -> str:
    focus = ">" if pane.id == active else " "
    messages = [f"    {m.source}" for m in pane.query_one(ChatLog).query(Markdown)]
    return "\n".join([f"{focus} {pane.id}", *messages])
