from textual.app import App, ComposeResult
from textual.widgets import Markdown

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentChangedEvent,
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantSaidEvent,
    SessionClearedEvent,
)
from simple_agent.application.on_complete import OnComplete
from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs
from simple_agent.infrastructure.textual.widgets.agent_tree import AgentTree
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog
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
        name = agent.rsplit("/", 1)[-1]
        self._tabs.handle_event(
            AgentStartedEvent(AgentId(agent), name, on_complete=OnComplete.CLOSE)
        )
        await self._pilot.pause()

    async def rename(self, agent: str, name: str) -> None:
        self._tabs.handle_event(AgentChangedEvent(AgentId(agent), new_name=name))
        await self._pilot.pause()

    async def focus(self, agent: str) -> None:
        self._tabs.activate_tab(AgentId(agent))
        await self._pilot.pause()

    async def select(self, agent: str) -> None:
        tree = self._tabs.active_workspace.query_one(AgentTree)
        node = _node_of(tree, AgentId(agent))
        await self._pilot.click(tree, offset=(6, node.line))
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
            _outline(pane, self._tabs.current)
            for pane in self._tabs.query_children(AgentWorkspace)
        )

    def trees(self) -> str:
        return "\n".join(
            f"{pane.id}\n{_tree(pane)}"
            for pane in self._tabs.query_children(AgentWorkspace)
        )

    def tree(self, agent: str) -> str:
        tab_id, _, _ = self._tabs.panel_ids_for(AgentId(agent))
        return _tree(self._tabs.get_child_by_id(tab_id))


def _tree(pane: AgentWorkspace) -> str:
    tree = pane.query_one(AgentTree)
    return "\n".join(_tree_lines(tree.root, tree.cursor_node, depth=-1))


def _outline(pane: AgentWorkspace, active: str) -> str:
    focus = ">" if pane.id == active else " "
    messages = [
        f"    {m.source}" for m in pane.query_one(ToolLog).query_children(Markdown)
    ]
    return "\n".join([f"{focus} {pane.id}", *messages])


def _tree_lines(node, cursor, depth: int) -> list[str]:
    highlight = ">" if node is cursor else " "
    lines = [f"{highlight} {'  ' * depth}{node.label.plain}"] if depth >= 0 else []
    for child in node.children:
        lines += _tree_lines(child, cursor, depth + 1)
    return lines


def _node_of(tree: AgentTree, agent_id: AgentId):
    def walk(node):
        if node.data == agent_id:
            return node
        return next(filter(None, map(walk, node.children)), None)

    return walk(tree.root)
