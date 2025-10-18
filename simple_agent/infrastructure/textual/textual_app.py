from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import RichLog, Input, TabbedContent, TabPane


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
    }

    #right-panel {
        width: 50%;
        height: 100%;
    }

    RichLog {
        background: $surface;
        color: $text;
        border: solid $primary;
        height: 100%;
        width: 100%;
    }

    #tool-results {
        background: $surface;
        color: $text;
        border: solid $primary;
        height: 100%;
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

    def compose(self) -> ComposeResult:
        with Vertical():
            with TabbedContent(id="tabs"):
                with TabPane("Agent", id="agent-tab"):
                    yield self.create_agent_container("log", "tool-results")
            yield Input(placeholder="Enter your message...", id="user-input", valid_empty=True)

    def create_agent_container(self, log_id, tool_results_id):
        return Horizontal(
            VerticalScroll(
                RichLog(highlight=True, markup=True, wrap=True, id=log_id),
                id="left-panel"
            ),
            VerticalScroll(
                RichLog(highlight=True, markup=True, id=tool_results_id),
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

    def write_message(self, message: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(message, width=log.size.width)

    def write_tool_result(self, message: str) -> None:
        tool_log = self.query_one("#tool-results", RichLog)
        tool_log.write(message, width=tool_log.size.width)

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

    def write_to_tab(self, log_id: str, message: str) -> None:
        log = self.query_one(f"#{log_id}", RichLog)
        log.write(message, width=log.size.width)

    def write_tool_result_to_tab(self, tool_results_id: str, message: str) -> None:
        tool_log = self.query_one(f"#{tool_results_id}", RichLog)
        tool_log.write(message, width=tool_log.size.width)

    def remove_subagent_tab(self, agent_id: str) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_id = f"tab-{agent_id.replace('/', '-')}"
        tabs.remove_pane(tab_id)

