import asyncio
import logging
from pathlib import Path
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)

from rich.syntax import Syntax
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.timer import Timer
from textual.containers import Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.geometry import Offset, Size
from textual.widgets import Static, TabbedContent, TabPane, TextArea, Collapsible, Markdown

from simple_agent.application.agent_id import AgentId
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.events import (
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    ErrorEvent,
    SessionClearedEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolCancelledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.application.tool_results import ToolResult
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from simple_agent.infrastructure.textual.resizable_container import ResizableHorizontal, ResizableVertical


def calculate_autocomplete_position(
    cursor_offset: Offset,
    screen_size: Size,
    popup_height: int,
    popup_width: int,
) -> Offset:
    if popup_height < 1:
        popup_height = 1
    if popup_width < 1:
        popup_width = 1

    below_y = cursor_offset.y + 1
    above_y = cursor_offset.y - popup_height

    if below_y + popup_height <= screen_size.height:
        y = below_y
    elif above_y >= 0:
        y = above_y
    else:
        y = max(0, min(below_y, screen_size.height - popup_height))

    anchor_x = cursor_offset.x - 2
    max_x = max(0, screen_size.width - popup_width)
    x = min(max(anchor_x, 0), max_x)
    return Offset(x, y)


class AutocompletePopup(Static):
    DEFAULT_CSS = """
    AutocompletePopup {
        background: $surface;
        color: $text;
        padding: 0 1;
        overlay: screen;
        layer: overlay;
        display: none;
    }
    """

    def show_suggestions(
        self,
        lines: list[str],
        selected_index: int,
        cursor_offset: Offset,
        screen_size: Size,
    ) -> None:
        if not lines:
            self.hide()
            return

        max_line_length = max(len(line) for line in lines)
        popup_width = min(max_line_length + 2, screen_size.width)
        available_width = max(1, popup_width - 2)
        trimmed_lines = [line[:available_width] for line in lines]
        popup_height = len(trimmed_lines)

        self.styles.width = popup_width
        self.styles.height = popup_height
        self.absolute_offset = calculate_autocomplete_position(
            cursor_offset=cursor_offset,
            screen_size=screen_size,
            popup_height=popup_height,
            popup_width=popup_width,
        )

        rendered = Text()
        for index, line in enumerate(trimmed_lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == selected_index else ""
            rendered.append(line, style=style)

        self.update(rendered)
        self.display = True

    def hide(self) -> None:
        self.display = False


class SubmittableTextArea(TextArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slash_command_registry = None
        self._autocomplete_visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._autocomplete_anchor_x = None

    def _on_key(self, event: events.Key) -> None:
        # Handle Tab for autocomplete
        if event.key == "tab" and self._autocomplete_visible:
            self._complete_selected_command()
            event.stop()
            event.prevent_default()
            return

        # Handle arrow keys for autocomplete navigation
        if event.key in ("down", "up") and self._autocomplete_visible:
            self._navigate_autocomplete(event.key)
            event.stop()
            event.prevent_default()
            return

        # Handle escape to close autocomplete
        if event.key == "escape" and self._autocomplete_visible:
            self._hide_autocomplete()
            event.stop()
            event.prevent_default()
            return

        # Let Enter submit the form
        if event.key == "enter":
            self.app.action_submit_input()
            event.stop()
            event.prevent_default()
            return
        # ctrl+j is how Windows/mintty sends Ctrl+Enter - insert newline
        if event.key in ("ctrl+enter", "ctrl+j"):
            # Explicitly insert newline
            self.insert("\n")
            event.stop()
            event.prevent_default()
            return

        # IMPORTANT: Call super()._on_key() first to let the character be inserted
        super()._on_key(event)

        # THEN check for autocomplete (now self.text will include the new character)
        self.call_after_refresh(self._check_autocomplete)

    def _check_autocomplete(self) -> None:
        """Check if we should show autocomplete based on current text."""
        if not self.slash_command_registry:
            return

        text = self.text

        if text.startswith("/"):
            self._show_autocomplete(text)
        else:
            self._hide_autocomplete()

    def _show_autocomplete(self, text: str) -> None:
        """Show autocomplete suggestions."""
        # Extract the command part (first word)
        command = text.split()[0] if text else text
        suggestions = self.slash_command_registry.get_matching_commands(command)

        logger.debug(f"Autocomplete for '{text}' (command: '{command}'): {len(suggestions)} suggestions")

        if suggestions:
            was_visible = self._autocomplete_visible
            self._autocomplete_visible = True
            self._current_suggestions = suggestions
            self._selected_index = 0
            if not was_visible:
                self._autocomplete_anchor_x = self.cursor_screen_offset.x
            self._update_autocomplete_display()
        else:
            self._hide_autocomplete()

    def _hide_autocomplete(self) -> None:
        """Hide autocomplete suggestions."""
        self._autocomplete_visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._autocomplete_anchor_x = None
        self._update_autocomplete_display()

    def _navigate_autocomplete(self, direction: str) -> None:
        """Navigate autocomplete suggestions with arrow keys."""
        if not self._current_suggestions:
            return

        if direction == "down":
            self._selected_index = (self._selected_index + 1) % len(self._current_suggestions)
        elif direction == "up":
            self._selected_index = (self._selected_index - 1) % len(self._current_suggestions)

        self._update_autocomplete_display()

    def _complete_selected_command(self) -> None:
        """Complete the selected command."""
        if not self._current_suggestions or self._selected_index >= len(self._current_suggestions):
            return

        selected = self._current_suggestions[self._selected_index]
        # Replace the current text with the selected command
        self.text = selected.name + " "
        self.move_cursor_relative(columns=len(selected.name) + 1)
        self._hide_autocomplete()

    def _update_autocomplete_display(self) -> None:
        """Update the autocomplete display in the popup."""
        try:
            popup = self.app.query_one("#autocomplete-popup", AutocompletePopup)
        except (NoMatches, AttributeError):
            popup = None

        if self._autocomplete_visible and self._current_suggestions:
            lines = [
                f"{cmd.name} - {cmd.description}"
                for cmd in self._current_suggestions
            ]
            if popup:
                anchor_x = self._autocomplete_anchor_x
                cursor_offset = self.cursor_screen_offset
                if anchor_x is not None:
                    cursor_offset = Offset(anchor_x, cursor_offset.y)
                popup.show_suggestions(
                    lines=lines,
                    selected_index=self._selected_index,
                    cursor_offset=cursor_offset,
                    screen_size=self.app.screen.size,
                )
        elif popup:
            popup.hide()

        try:
            hint_widget = self.app.query_one("#input-hint", Static)
            hint_widget.update("Enter to submit, Ctrl+Enter for newline")
        except (NoMatches, AttributeError):
            pass



class TextualApp(App):

    async def run_with_session_async(self, session_runner: Callable[[], Coroutine[Any, Any, None]]):
        self._session_runner = session_runner
        return await self.run_async()

    def shutdown(self):
        if self.is_running:
            self.exit()
    BINDINGS = [
        ("alt+left", "previous_tab", "Previous Tab"),
        ("alt+right", "next_tab", "Next Tab"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("enter", "submit_input", "Submit"),
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
        width: 25%;
        padding: 1;
    }

    .left-panel-top,
    .left-panel-bottom {
        min-height: 0;
    }

    .left-panel-bottom {
        background: $surface-darken-1;
        overflow-y: auto;
        padding: 1 1 0 1;
    }

    #right-panel {
        width: 75%;
        padding: 1;
    }

    .tool-call {
        color: $primary;
        text-style: bold;
    }

    .tool-result {
        background: $surface;
    }

    .tool-result-error {
        border: round $error;
    }

    .tool-result-success {
        border: round $success;
    }

    Pretty {
        border: round $primary;
        margin-bottom: 1;
    }

    #user-input {
        height: 5;
        min-height: 3;
        max-height: 10;
        border: solid $primary;
    }

    #input-hint {
        height: 1;
        color: $text-muted;
        text-align: right;
        padding-right: 1;
    }
    """

    def __init__(self, user_input=None, root_agent_id: AgentId = AgentId("Agent")):
        super().__init__()
        self.user_input = user_input
        self._root_agent_id = root_agent_id
        self._session_runner: Callable[[], Coroutine[Any, Any, None]] | None = None
        self._session_task: asyncio.Task | None = None
        self._pending_tool_calls: dict[str, dict[str, tuple[str, TextArea, Collapsible]]] = {}
        self._tool_result_collapsibles: dict[str, list[Collapsible]] = {}
        self._agent_panel_ids: dict[AgentId, tuple[str, str]] = {}
        self._agent_names: dict[AgentId, str] = {root_agent_id: root_agent_id.raw}
        self._todo_widgets: dict[str, Markdown] = {}
        self._todo_containers: dict[str, tuple] = {}
        self._tool_results_to_agent: dict[str, AgentId] = {}
        self._slash_command_registry = SlashCommandRegistry()
        self._agent_models: dict[AgentId, str] = {root_agent_id: ""}
        self._agent_max_tokens: dict[AgentId, int] = {root_agent_id: 0}
        self._suppressed_tool_calls: set[str] = set()
        self.loading_timer: Timer | None = None
        self.loading_frames = ["⠇", "⠏", "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]
        self.loading_frame_index = 0

    def has_agent_tab(self, agent_id: AgentId) -> bool:
        return agent_id in self._agent_panel_ids

    @staticmethod
    def panel_ids_for(agent_id: AgentId) -> tuple[str, str, str]:
        sanitized = agent_id.for_ui()
        tab_id = f"tab-{sanitized}"
        log_id = f"log-{sanitized}"
        tool_results_id = f"tool-results-{sanitized}"
        return tab_id, log_id, tool_results_id

    def compose(self) -> ComposeResult:
        tab_id, log_id, tool_results_id = self.panel_ids_for(self._root_agent_id)
        with Vertical():
            with TabbedContent(id="tabs"):
                with TabPane(self._root_agent_id.raw, id=tab_id):
                    yield self.create_agent_container(log_id, tool_results_id, self._root_agent_id)
            yield Static("Enter to submit, Ctrl+Enter for newline", id="input-hint")
            yield SubmittableTextArea(id="user-input")
            yield AutocompletePopup(id="autocomplete-popup")

    def create_agent_container(self, log_id, tool_results_id, agent_id):
        chat_scroll = VerticalScroll(id=f"{log_id}-scroll", classes="left-panel-top")
        todo = Markdown(self._load_todos(agent_id), id=f"{log_id}-todos")
        secondary_scroll = VerticalScroll(todo, id=f"{log_id}-secondary", classes="left-panel-bottom")

        left_panel = ResizableVertical(chat_scroll, secondary_scroll, id="left-panel")

        todo_content = self._load_todos(agent_id)
        if not todo_content:
            secondary_scroll.styles.display = "none"
            left_panel.splitter.styles.display = "none"

        self._todo_containers[str(agent_id)] = (secondary_scroll, left_panel.splitter)

        right_panel = VerticalScroll(id=tool_results_id)
        self._tool_result_collapsibles[tool_results_id] = []
        self._agent_panel_ids[agent_id] = (log_id, tool_results_id)
        self._tool_results_to_agent[tool_results_id] = agent_id
        self._todo_widgets[str(agent_id)] = todo
        self._pending_tool_calls[tool_results_id] = {}
        return ResizableHorizontal(left_panel, right_panel, id="tab-content")

    async def on_mount(self) -> None:
        text_area = self.query_one("#user-input", SubmittableTextArea)
        text_area.slash_command_registry = self._slash_command_registry
        text_area.focus()
        if self._session_runner:
            self._session_task = asyncio.create_task(self._run_session())

    async def _run_session(self) -> None:
        """Run the session and exit the app when done."""
        try:
            await self._session_runner()
        except Exception as e:
            logger.error("Session error: %s", e)
        self.exit()

    def on_unmount(self) -> None:
        if self.user_input:
            self.user_input.close()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            if self._session_task and not self._session_task.done():
                self._session_task.cancel()
            event.prevent_default()
            return
        # Enter is now handled by SubmittableTextArea
        return

    def action_quit(self) -> None:
        """Ensure Ctrl+C / Ctrl+Q stop the agent, not just the UI."""
        if self.user_input:
            self.user_input.close()
        if self._session_task and not self._session_task.done():
            self._session_task.cancel()
        self.exit()

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

    def action_submit_input(self) -> None:
        text_area = self.query_one("#user-input", SubmittableTextArea)
        content = text_area.text.strip()
        if self.user_input:
            self.user_input.submit_input(content)
        text_area.clear()
        text_area._hide_autocomplete()

    def write_message(self, log_id: str, message: str) -> None:
        try:
            scroll = self.query_one(f"#{log_id}-scroll", VerticalScroll)
            msg_widget = Markdown(message.rstrip())
            scroll.mount(msg_widget)
            scroll.scroll_end(animate=False)
        except NoMatches:
            logger.warning("Could not find scroll container #%s-scroll", log_id)
        except Exception as e:
            logger.error("Failed to display message: %s. Message: %s", e, message)

    def _update_loading_animation(self) -> None:
        frame = self.loading_frames[self.loading_frame_index]
        for panel_tool_calls in self._pending_tool_calls.values():
            for _, text_area, _ in panel_tool_calls.values():
                text_area.load_text(f"In Progress {frame}")
                text_area.refresh()
        self.loading_frame_index = (self.loading_frame_index + 1) % len(self.loading_frames)

    def _stop_loading_if_idle(self) -> None:
        if not any(self._pending_tool_calls.values()):
            if self.loading_timer:
                self.loading_timer.stop()
                self.loading_timer = None

    def _pop_pending_tool_call(
        self,
        tool_results_id: str,
        call_id: str,
    ) -> tuple[tuple[str, TextArea, Collapsible] | None, bool]:
        pending_for_panel = self._pending_tool_calls.setdefault(tool_results_id, {})
        if call_id in self._suppressed_tool_calls:
            self._suppressed_tool_calls.discard(call_id)
            pending_for_panel.pop(call_id, None)
            self._refresh_todos(tool_results_id)
            return None, True
        return pending_for_panel.pop(call_id, None), False

    def write_tool_call(self, tool_results_id: str, call_id: str, message: str) -> None:
        pending_for_panel = self._pending_tool_calls.setdefault(tool_results_id, {})
        if "write-todos" in message:
            pending_for_panel.pop(call_id, None)
            self._suppressed_tool_calls.add(call_id)
            return
        try:
            container = self.query_one(f"#{tool_results_id}", VerticalScroll)
        except NoMatches:
            logger.warning("Could not find tool results container #%s", tool_results_id)
            return
        collapsibles = self._tool_result_collapsibles.setdefault(tool_results_id, [])
        for collapsible in collapsibles:
            collapsible.collapsed = True

        text_area = TextArea(
            f"In Progress {self.loading_frames[0]}",
            read_only=True,
            language="markdown",
            show_cursor=False,
            classes="tool-call",
        )
        text_area.styles.height = 3
        text_area.styles.min_height = 3

        lines = message.splitlines()
        default_title = lines[0] if lines else "Tool Call"
        collapsible = Collapsible(text_area, title=default_title, collapsed=False)
        collapsibles.append(collapsible)
        container.mount(collapsible)
        container.scroll_end(animate=False)

        pending_for_panel[call_id] = (message, text_area, collapsible)
        if not self.loading_timer:
            self.loading_timer = self.set_interval(0.1, self._update_loading_animation)

    def write_tool_result(self, tool_results_id: str, call_id: str, result: ToolResult) -> None:
        success = result.success
        pending_entry, suppressed = self._pop_pending_tool_call(tool_results_id, call_id)
        if suppressed:
            return
        if pending_entry is None:
            logger.warning(
                "Tool result received with no matching call. tool_results_id=%s call_id=%s",
                tool_results_id,
                call_id,
            )
            self._refresh_todos(tool_results_id)
            self._stop_loading_if_idle()
            return
        title_source, text_area, call_collapsible = pending_entry
        message = result.display_body if result.display_body else result.message
        message = message or ""
        title_text = result.display_title if result.display_title else None
        lines = title_source.splitlines()
        default_title = lines[0] if lines else "Tool Result"
        other_lines = lines[1:]
        if title_text is None:
            title_text = default_title
        if success and other_lines and not result.display_body and not message.strip():
            message = "\n".join(other_lines)

        collapsibles = self._tool_result_collapsibles.setdefault(tool_results_id, [])
        for existing in collapsibles:
            existing.collapsed = True
        call_collapsible.collapsed = False

        classes = "tool-result tool-result-success" if success else "tool-result tool-result-error"
        language = result.display_language or "python"

        if language == "diff":
            diff_renderable = Syntax(
                message,
                "diff",
                theme="ansi_dark",
                line_numbers=False,
                word_wrap=True,
            )
            diff_widget = Static(diff_renderable)
            for cls in classes.split():
                diff_widget.add_class(cls)
            height = min((len(message.splitlines()) or 1) + 2, 30)
            diff_widget.styles.height = height
            diff_widget.styles.min_height = height
            text_area.remove()
            try:
                contents = call_collapsible.query_one(Collapsible.Contents)
                contents.mount(diff_widget)
            except NoMatches:
                logger.warning(
                    "Missing collapsible contents for tool result. tool_results_id=%s call_id=%s",
                    tool_results_id,
                    call_id,
                )
                call_collapsible.mount(diff_widget)
        else:
            line_count = len(message.splitlines()) or 1
            height = min(line_count + 2, 30)
            text_area.load_text(message)
            text_area.language = language
            text_area.remove_class("tool-call")
            for cls in ("tool-result", "tool-result-error"):
                text_area.remove_class(cls)
            for cls in classes.split():
                text_area.add_class(cls)
            text_area.styles.height = height
            text_area.styles.min_height = height

        call_collapsible.title = title_text
        container = self.query_one(f"#{tool_results_id}", VerticalScroll)
        container.scroll_end(animate=False)
        self._refresh_todos(tool_results_id)
        self._stop_loading_if_idle()

    def write_tool_cancelled(self, tool_results_id: str, call_id: str) -> None:
        pending_entry, suppressed = self._pop_pending_tool_call(tool_results_id, call_id)
        if suppressed:
            self._stop_loading_if_idle()
            return
        if pending_entry is None:
            logger.warning(
                "Tool cancelled with no matching call. tool_results_id=%s call_id=%s",
                tool_results_id,
                call_id,
            )
            self._stop_loading_if_idle()
            return
        title_source, text_area, call_collapsible = pending_entry

        # Update to show cancelled state
        text_area.load_text("Cancelled")
        text_area.remove_class("tool-call")
        text_area.add_class("tool-result")
        text_area.add_class("tool-result-error")
        text_area.styles.height = 3
        text_area.styles.min_height = 3

        lines = title_source.splitlines()
        default_title = lines[0] if lines else "Tool Call"
        call_collapsible.title = f"{default_title} (Cancelled)"

        container = self.query_one(f"#{tool_results_id}", VerticalScroll)
        container.scroll_end(animate=False)

        self._stop_loading_if_idle()

    def add_subagent_tab(self, agent_id: AgentId, tab_title: str) -> tuple[str, str]:
        tab_id, log_id, tool_results_id = self.panel_ids_for(agent_id)

        agent_name = tab_title.split(" [")[0] if " [" in tab_title else tab_title
        self._agent_names[agent_id] = agent_name

        new_tab = TabPane(tab_title, id=tab_id)
        new_tab.compose_add_child(self.create_agent_container(log_id, tool_results_id, agent_id))

        tabs = self.query_one("#tabs", TabbedContent)
        tabs.add_pane(new_tab)
        tabs.active = tab_id
        return log_id, tool_results_id

    def remove_subagent_tab(self, agent_id: AgentId) -> None:
        tab_id, _, tool_results_id = self.panel_ids_for(agent_id)
        self.query_one("#tabs", TabbedContent).remove_pane(tab_id)
        panel_ids = self._agent_panel_ids.pop(agent_id, None)
        if panel_ids:
            self._tool_result_collapsibles.pop(tool_results_id, None)
            self._pending_tool_calls.pop(tool_results_id, None)
            self._tool_results_to_agent.pop(tool_results_id, None)
            prefix = f"{agent_id}::tool_call::"
            self._suppressed_tool_calls = {
                call_id for call_id in self._suppressed_tool_calls if not call_id.startswith(prefix)
            }
        self._agent_names.pop(agent_id, None)
        self._todo_widgets.pop(str(agent_id), None)
        self._todo_containers.pop(str(agent_id), None)

    def _load_todos(self, agent_id: AgentId) -> str:
        path = Path(agent_id.todo_filename())
        if not path.exists():
            return ""
        content = path.read_text(encoding="utf-8").strip()
        return content if content else ""

    def _refresh_todos(self, tool_results_id: str) -> None:
        agent_id = self._tool_results_to_agent.get(tool_results_id)
        if not agent_id:
            return
        self._refresh_todos_for_agent(agent_id)

    def _refresh_todos_for_agent(self, agent_id: AgentId) -> None:
        todo_widget = self._todo_widgets.get(str(agent_id))
        if not todo_widget:
            return
        todo_content = self._load_todos(agent_id)
        todo_widget.update(todo_content)

        container_tuple = self._todo_containers.get(str(agent_id))
        if container_tuple:
            secondary_scroll, splitter = container_tuple
            if todo_content:
                secondary_scroll.styles.display = "block"
                splitter.styles.display = "block"
            else:
                secondary_scroll.styles.display = "none"
                splitter.styles.display = "none"

    def update_tab_title(self, agent_id: AgentId, title: str) -> None:
        tab_id, _, _ = self.panel_ids_for(agent_id)
        try:
            tabs = self.query_one("#tabs", TabbedContent)
            tab = tabs.get_tab(tab_id)
            if tab:
                tab.label = title
        except (NoMatches, Exception):
            pass

    def _ensure_agent_tab_exists(self, agent_id: AgentId, agent_name: str | None, model: str) -> None:
        if not self.is_running:
            return
        if agent_name:
            self._agent_names[agent_id] = agent_name
        if model is not None:
            self._agent_models[agent_id] = model
        if self.has_agent_tab(agent_id):
            if model:
                title = self._tab_title_for(agent_id, model, 0, self._agent_max_tokens.get(agent_id, 0))
                self.update_tab_title(agent_id, title)
            return
        tab_title = self._tab_title_for(agent_id, model, 0, 0)
        self.add_subagent_tab(agent_id, tab_title)

    def on_domain_event_message(self, message: DomainEventMessage) -> None:
        event = message.event
        if isinstance(event, AgentStartedEvent):
            self._ensure_agent_tab_exists(event.agent_id, event.agent_name, event.model)
        elif isinstance(event, SessionClearedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            self.clear_agent_panels(log_id)
            self._clear_todo_panel(event.agent_id)
            self._reset_agent_token_usage(event.agent_id)
        elif isinstance(event, UserPromptedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            self.write_message(log_id, f"**User:** {event.input_text}")
        elif isinstance(event, AssistantSaidEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            agent_name = self._agent_names.get(event.agent_id, str(event.agent_id))
            self.write_message(log_id, f"**{agent_name}:** {event.message}")
        elif isinstance(event, ToolCalledEvent):
            _, _, tool_results_id = self.panel_ids_for(event.agent_id)
            self.write_tool_call(tool_results_id, event.call_id, event.tool.header())
        elif isinstance(event, ToolResultEvent):
            if not event.result:
                return
            _, _, tool_results_id = self.panel_ids_for(event.agent_id)
            self.write_tool_result(tool_results_id, event.call_id, event.result)
        elif isinstance(event, ToolCancelledEvent):
            _, _, tool_results_id = self.panel_ids_for(event.agent_id)
            self.write_tool_cancelled(tool_results_id, event.call_id)
        elif isinstance(event, SessionInterruptedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            self.write_message(log_id, "\n[Session interrupted by user]")
        elif isinstance(event, SessionStartedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            if event.is_continuation:
                self.write_message(log_id, "Continuing session")
            else:
                self.write_message(log_id, "Starting new session")
        elif isinstance(event, SessionEndedEvent):
            if self.is_running and self.has_agent_tab(event.agent_id):
                self.remove_subagent_tab(event.agent_id)
        elif isinstance(event, UserPromptRequestedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            self.write_message(log_id, "\nWaiting for user input...")
        elif isinstance(event, ErrorEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            self.write_message(log_id, f"\n**❌ Error: {event.message}**")
        elif isinstance(event, AssistantRespondedEvent):
            self._agent_models[event.agent_id] = event.model
            self._agent_max_tokens[event.agent_id] = event.max_tokens
            title = self._tab_title_for(event.agent_id, event.model, event.token_count, event.max_tokens)
            self.update_tab_title(event.agent_id, title)

    def _tab_title_for(self, agent_id: AgentId, model: str, token_count: int, max_tokens: int) -> str:
        base_title = self._agent_names.get(agent_id, str(agent_id))

        if not model:
            return base_title

        if max_tokens == 0:
            return f"{base_title} [{model}: 0.0%]"

        percentage = (token_count / max_tokens) * 100
        return f"{base_title} [{model}: {percentage:.1f}%]"

    def clear_agent_panels(self, log_id: str) -> None:
        # Clear chat scroll area
        try:
            chat_scroll = self.query_one(f"#{log_id}-scroll", VerticalScroll)
            chat_scroll.remove_children()
        except NoMatches:
            logger.warning("Could not find chat scroll #%s-scroll to clear", log_id)

        # Clear tool results panel
        tool_results_id = log_id.replace("log-", "tool-results-")
        try:
            tool_results = self.query_one(f"#{tool_results_id}", VerticalScroll)
            tool_results.remove_children()
            # Clear tracking state for this panel
            self._tool_result_collapsibles[tool_results_id] = []
            self._pending_tool_calls[tool_results_id] = {}
        except NoMatches:
            logger.warning("Could not find tool results #%s to clear", tool_results_id)

    def _clear_todo_panel(self, agent_id: AgentId) -> None:
        todo_widget = self._todo_widgets.get(str(agent_id))
        if todo_widget:
            todo_widget.update("")

        container_tuple = self._todo_containers.get(str(agent_id))
        if container_tuple:
            secondary_scroll, splitter = container_tuple
            secondary_scroll.styles.display = "none"
            splitter.styles.display = "none"

    def _reset_agent_token_usage(self, agent_id: AgentId) -> None:
        model = self._agent_models.get(agent_id, "")
        max_tokens = self._agent_max_tokens.get(agent_id, 0)
        title = self._tab_title_for(agent_id, model, 0, max_tokens)
        self.update_tab_title(agent_id, title)
