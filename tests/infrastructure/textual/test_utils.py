import io
from rich.console import Console
from textual.widgets import TextArea, Static, Collapsible, Markdown
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.widgets.todo_view import TodoView

class MockUserInput:
    def __init__(self):
        self.submitted_content = []

    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def submit_input(self, content: str) -> None:
        self.submitted_content.append(content)

    def close(self) -> None:
        pass

def dump_ui_state(app: TextualApp) -> str:
    lines = []

    # Dump Tabs
    tabs = app.query("TabPane")
    lines.append(f"Tabs: {[t.id for t in tabs]}")
    lines.append(f"Active Tab: {app.query_one('TabbedContent').active}")

    # Dump Visible Widgets in Main Content
    for widget in app.screen.walk_children():
        indent = "  " * len(list(widget.ancestors))
        classes = sorted(list(widget.classes))
        class_name = widget.__class__.__name__
        if isinstance(widget, TodoView):
            class_name = "VerticalScroll"
        info = f"{indent}{class_name} id='{widget.id}' classes='{' '.join(classes)}'"

        if isinstance(widget, Markdown):
             # Markdown content isn't easily accessible as raw text directly from widget.source
             # but we can try accessing the source if available
             info += f" source={repr(widget.source[:50])}..."

        if isinstance(widget, TextArea):
            info += f" text={repr(widget.text)}"

        if isinstance(widget, Collapsible):
            info += f" title={repr(widget.title)} collapsed={widget.collapsed}"

        if isinstance(widget, Static) and not isinstance(widget, (Markdown, TextArea)):
             # Try to get text from renderable if it's simple
             if hasattr(widget, "renderable") and hasattr(widget.renderable, "plain"):
                 info += f" content={repr(widget.renderable.plain)}"

        lines.append(info)

    return "\n".join(lines)

def dump_ascii_screen(app: TextualApp) -> str:
    """Capture the ASCII representation of the current screen."""
    console = Console(
        record=True,
        width=app.size.width,
        height=app.size.height,
        force_terminal=False,
        file=io.StringIO(),
        color_system=None,
        legacy_windows=False,
        safe_box=False,
    )
    console.print(app.screen._compositor)
    output = console.export_text()

    # Clean up output
    # 1. Strip trailing whitespace from each line
    lines = [line.rstrip() for line in output.splitlines()]

    # 2. Normalize horizontal splitter (flaky rendering across environments)
    # The splitter typically renders as a mix of '━' and '╸' or '╺'.
    # We'll replace lines that look like horizontal splitters with a stable representation.
    normalized_lines = []
    for line in lines:
        if "━" in line and ("╸" in line or "╺" in line):
             # Heuristic: if a line is mostly splitter chars, replace it
             if len(line) > 10 and all(c in " ━╸╺" for c in line.strip()):
                 # Replace with a solid line of the same length
                 normalized_lines.append("━" * len(line))
                 continue
        normalized_lines.append(line)

    return "\n".join(normalized_lines)
