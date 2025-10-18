from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Input, TabbedContent, TabPane


class TextualApp(App):

    CSS = """
    Screen {
        background: $surface;
    }

    TabbedContent {
        height: 1fr;
    }

    #tab-content {
        height: 1fr;
    }

    #left-panel {
        width: 50%;
        height: 100%;
        border-right: solid $surface-lighten-1;
        padding: 1;
    }

    #right-panel {
        width: 50%;
        height: 100%;
        padding: 1;
    }

    #messages-container {
        background: $surface;
        color: $text;
        border: solid $primary;
        height: 100%;
        width: 100%;
    }

    .message {
        margin-bottom: 1;
        padding: 1;
        background: $panel;
        border: solid $primary-lighten-1;
    }

    .message-role {
        color: $accent;
        text-style: bold;
    }

    .message-content {
        color: $text;
        margin-top: 1;
    }

    #tool-results-container {
        background: $surface;
        color: $text;
        border: solid $primary;
        height: 100%;
        padding: 1;
    }

    #user-input {
        height: 3;
        width: 100%;
        border: solid $primary;
    }
    """

    def __init__(self, user_input=None):
        super().__init__()
        self.user_input = user_input
        self._content_cache = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            with TabbedContent(id="tabs"):
                with TabPane("Agent", id="agent-tab"):
                    yield self.create_agent_container("log", "tool-results")
            yield Input(placeholder="Enter your message...", id="user-input", valid_empty=True)

    def create_agent_container(self, log_id, tool_results_id):
        return Horizontal(
            VerticalScroll(
                Static("", id=log_id, classes="messages-container"),
                id="left-panel"
            ),
            VerticalScroll(
                Static("", id=tool_results_id, classes="tool-results-container"),
                id="right-panel"
            ),
            id="tab-content"
        )

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

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.user_input:
            self.user_input.submit_input(event.value.strip())
        event.input.value = ""

    def write_message(self, log_id: str, message: str) -> None:
        container = self.query_one(f"#{log_id}", Static)
        current = self._content_cache.get(log_id, "")
        if current:
            new_content = f"{current}\n{message}"
        else:
            new_content = message
        self._content_cache[log_id] = new_content
        container.update(new_content)
        scroll_container = self.query_one("#left-panel", VerticalScroll)
        scroll_container.scroll_end(animate=False)

    def write_tool_result(self, tool_results_id: str, message: str) -> None:
        container = self.query_one(f"#{tool_results_id}", Static)
        current = self._content_cache.get(tool_results_id, "")
        if current:
            new_content = f"{current}\n{message}"
        else:
            new_content = message
        self._content_cache[tool_results_id] = new_content
        container.update(new_content)
        scroll_container = self.query_one("#right-panel", VerticalScroll)
        scroll_container.scroll_end(animate=False)

    def add_subagent_tab(self, agent_id: str, tab_title: str) -> tuple[str, str]:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_id = f"tab-{agent_id.replace('/', '-')}"
        log_id = f"log-{agent_id.replace('/', '-')}"
        tool_results_id = f"tool-results-{agent_id.replace('/', '-')}"

        new_tab = TabPane(tab_title, id=tab_id)
        new_tab.compose_add_child(
            self.create_agent_container(log_id, tool_results_id)
        )
        tabs.add_pane(new_tab)
        tabs.active = tab_id
        return log_id, tool_results_id

    def remove_subagent_tab(self, agent_id: str) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_id = f"tab-{agent_id.replace('/', '-')}"
        tabs.remove_pane(tab_id)

