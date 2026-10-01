from dataclasses import dataclass
from enum import Enum

from rich.text import Text
from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from simple_agent.application.agent_id import AgentId


class Lifecycle(Enum):
    RUNNING = ("●", "grey50")
    WAITING = ("●", "dark_orange")
    IDLE = ("○", "grey35")


class AgentTree(Tree[AgentId]):
    @dataclass
    class AgentSelected(Message):
        agent_id: AgentId

    def __init__(self, current: AgentId, **kwargs):
        super().__init__("agents", **kwargs)
        self.show_root = False
        self.auto_expand = False
        self._current = current

    def show_agents(
        self,
        names: dict[AgentId, str],
        lifecycles: dict[AgentId, Lifecycle] | None = None,
    ) -> None:
        lifecycles = lifecycles or {}
        self.clear()
        nodes = {}
        for agent_id, name in names.items():
            parent = nodes.get(_nearest_ancestor(agent_id, names), self.root)
            lifecycle = lifecycles.get(agent_id, Lifecycle.RUNNING)
            label = Text.assemble(lifecycle.value, " ", name)
            nodes[agent_id] = parent.add(label, data=agent_id, expand=True)
        for node in nodes.values():
            node.allow_expand = bool(node.children)
        self._highlight_current()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        event.stop()
        if event.node.data is not None:
            self.post_message(self.AgentSelected(event.node.data))
        self._highlight_current()

    def on_blur(self) -> None:
        self._highlight_current()

    def _highlight_current(self) -> None:
        lines = [node.data for node in _visible_nodes(self.root)]
        if self._current in lines:
            self.cursor_line = lines.index(self._current)


def _visible_nodes(node: TreeNode[AgentId]):
    for child in node.children:
        yield child
        if child.is_expanded:
            yield from _visible_nodes(child)


def _nearest_ancestor(agent_id: AgentId, known) -> AgentId | None:
    ancestor = agent_id.parent()
    while ancestor is not None and ancestor not in known:
        ancestor = ancestor.parent()
    return ancestor
