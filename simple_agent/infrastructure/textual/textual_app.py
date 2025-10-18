from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, Input, TabbedContent, TabPane, Pretty
from simple_agent.infrastructure.textual.resizable_container import ResizableHorizontal


class TextualApp(App):

    BINDINGS = [
        ("alt+left", "previous_tab", "Previous Tab"),
        ("alt+right", "next_tab", "Next Tab"),
    ]

    CSS = """
    TabbedContent {
        height: 1fr;
    }

    #tab-content {
        height: 1fr;
    }

    ResizableHorizontal {
        height: 1fr;
    }

    #left-panel {
        width: 50%;
        padding: 1;
    }

    #right-panel {
        width: 50%;
        padding: 1;
    }

    .tool-call {
        color: $accent;
        text-style: bold;
    }

    .tool-result {
        color: $text-muted;
    }

    Pretty {
        border: round $primary;
        margin-bottom: 1;
    }

    #user-input {
        height: 3;
        border: solid $primary;
    }
    """

    def __init__(self, user_input=None):
        super().__init__()
        self.user_input = user_input

    def compose(self) -> ComposeResult:
        with Vertical():
            with TabbedContent(id="tabs"):
                with TabPane("Agent", id="agent-tab"):
                    yield self.create_agent_container("log", "tool-results")
            yield Input(placeholder="Enter your message...", id="user-input", valid_empty=True)

    def create_agent_container(self, log_id, tool_results_id):
        left_panel = VerticalScroll(Static("", id=log_id), id="left-panel")
        right_panel = VerticalScroll(id=tool_results_id)
        return ResizableHorizontal(left_panel, right_panel, id="tab-content")

    def on_mount(self) -> None:
        self.query_one("#user-input", Input).focus()

    def on_unmount(self) -> None:
        if self.user_input:
            self.user_input.close()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            if self.user_input:
                self.user_input.request_escape()
            event.prevent_default()

    def action_previous_tab(self) -> None:
        self._switch_tab(-1)

    def action_next_tab(self) -> None:
        self._switch_tab(1)

    def _switch_tab(self, direction: int) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_panes = list(tabs.query(TabPane))
        if len(tab_panes) <= 1:
            return
        current_index = next((i for i, pane in enumerate(tab_panes) if pane.id == tabs.active), 0)
        new_index = (current_index + direction) % len(tab_panes)
        new_tab_id = tab_panes[new_index].id
        if new_tab_id:
            tabs.active = new_tab_id

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.user_input:
            self.user_input.submit_input(event.value.strip())
        event.input.value = ""

    def write_message(self, log_id: str, message: str) -> None:
        container = self.query_one(f"#{log_id}", Static)
        current = str(container.render())
        new_content = f"{current}\n{message}" if current else message
        container.update(new_content)
        self.query_one("#left-panel", VerticalScroll).scroll_end(animate=False)

    def write_tool_call(self, tool_results_id: str, message: str) -> None:
        container = self.query_one(f"#{tool_results_id}", VerticalScroll)
        container.mount(Static(f"[bold cyan]{message}[/bold cyan]"))
        container.scroll_end(animate=False)

    def write_tool_result(self, tool_results_id: str, message: str) -> None:
        container = self.query_one(f"#{tool_results_id}", VerticalScroll)
        container.mount(Pretty(message))
        container.scroll_end(animate=False)

    def add_subagent_tab(self, agent_id: str, tab_title: str) -> tuple[str, str]:
        sanitized = agent_id.replace('/', '-')
        tab_id = f"tab-{sanitized}"
        log_id = f"log-{sanitized}"
        tool_results_id = f"tool-results-{sanitized}"

        new_tab = TabPane(tab_title, id=tab_id)
        new_tab.compose_add_child(self.create_agent_container(log_id, tool_results_id))

        tabs = self.query_one("#tabs", TabbedContent)
        tabs.add_pane(new_tab)
        tabs.active = tab_id
        return log_id, tool_results_id

    def remove_subagent_tab(self, agent_id: str) -> None:
        tab_id = f"tab-{agent_id.replace('/', '-')}"
        self.query_one("#tabs", TabbedContent).remove_pane(tab_id)

