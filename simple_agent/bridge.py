#!/usr/bin/env python
import asyncio
import io
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.syntax import Syntax
from textual.widgets import Collapsible, Markdown, Static, TextArea

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ruff: noqa: E402
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace
from simple_agent.main import main_async

BRIDGE_DIR = Path("bridge")
INBOX = BRIDGE_DIR / "inbox"
OUTBOX = BRIDGE_DIR / "outbox"
STATUS_FILE = BRIDGE_DIR / "status"
INPUT_FILE = INBOX / "message.txt"
STATE_FILE = OUTBOX / "state.md"

_updater_task = None


def setup_bridge():
    if BRIDGE_DIR.exists():
        import shutil

        shutil.rmtree(BRIDGE_DIR)
    BRIDGE_DIR.mkdir()
    INBOX.mkdir()
    OUTBOX.mkdir()


def get_screen_content(app: TextualApp) -> str:
    """Captures the Textual screen as a plain text string."""
    string_io = io.StringIO()
    console = Console(
        file=string_io,
        force_terminal=False,
        width=120,
        height=40,
        legacy_windows=False,
        safe_box=False,
        record=False,  # No need to record, we capture from the file
    )
    console.print(app.screen._compositor)
    return string_io.getvalue()


def get_structured_state(app: TextualApp) -> dict:
    state = {
        "agent_id": None,
        "agent_name": None,
        "chat_history": [],
        "tool_log": [],
        "todos": "",
        "input": "",
    }

    try:
        tabs = app.query_one(AgentTabs)
        workspace = tabs.active_workspace
        if workspace and isinstance(workspace, AgentWorkspace):
            state["agent_id"] = str(workspace.agent_id)
            state["agent_name"] = tabs._agent_names.get(
                workspace.agent_id, str(workspace.agent_id)
            )

            # Chat History
            chat_messages = []
            for child in workspace.chat_log.children:
                if isinstance(child, Markdown):
                    chat_messages.append(child.source)
            state["chat_history"] = chat_messages

            # Tool Log
            tool_entries = []
            for collapsible in workspace.tool_log.children:
                if isinstance(collapsible, Collapsible):
                    entry = {
                        "title": str(collapsible.title),
                        "content": "",
                        "collapsed": collapsible.collapsed,
                    }
                    # Inspect content
                    # ToolLog adds a TextArea or Static(Syntax) inside the collapsible
                    # But Collapsible wraps content in a Container (Contents)
                    try:
                        contents = collapsible.query_one(Collapsible.Contents)
                        # The actual content widget is inside Contents
                        if contents.children:
                            widget = contents.children[0]
                            if isinstance(widget, TextArea):
                                entry["content"] = widget.text
                            elif isinstance(widget, Static) and isinstance(
                                widget.renderable, Syntax
                            ):
                                entry["content"] = widget.renderable.code
                    except Exception:
                        pass
                    tool_entries.append(entry)
            state["tool_log"] = tool_entries

            # Todo
            state["todos"] = workspace.todo_view.content

            # Input
            if workspace.smart_input:
                state["input"] = workspace.smart_input.value

    except Exception:
        pass

    return state


def format_state_as_markdown(screen_content: str, structured_data: dict) -> str:
    """Formats the application state as a Markdown string."""
    md_content = []
    md_content.append("# Agent State")
    md_content.append(f"Timestamp: {time.time()}\n")

    md_content.append("## Screen\n")
    md_content.append("```text")
    md_content.append(screen_content)
    md_content.append("```\n")

    md_content.append("## Data\n")
    if structured_data.get("agent_id"):
        md_content.append("### Agent Info")
        md_content.append(f"- **ID**: {structured_data['agent_id']}")
        md_content.append(f"- **Name**: {structured_data['agent_name']}\n")

    if structured_data.get("chat_history"):
        md_content.append("### Chat History")
        for msg in structured_data["chat_history"]:
            md_content.append("---\n" + msg)
        md_content.append("\n")

    if structured_data.get("tool_log"):
        md_content.append("### Tool Log")
        for entry in structured_data["tool_log"]:
            collapsed_str = " (collapsed)" if entry["collapsed"] else ""
            md_content.append(f"#### `{entry['title']}`{collapsed_str}")
            if not entry["collapsed"] and entry["content"]:
                md_content.append("```")
                md_content.append(entry["content"])
                md_content.append("```")
        md_content.append("\n")

    if structured_data.get("todos"):
        md_content.append("### TODOs")
        md_content.append(structured_data["todos"])
        md_content.append("\n")

    if "input" in structured_data and structured_data.get("input"):
        md_content.append("### Current Input")
        md_content.append("```")
        md_content.append(structured_data["input"])
        md_content.append("```")
        md_content.append("\n")

    return "\n".join(md_content)


def update_state_file(app: TextualApp):
    """Captures the current state and writes it to the state file."""
    try:
        screen_content = get_screen_content(app)
        structured_data = get_structured_state(app)
        markdown_output = format_state_as_markdown(screen_content, structured_data)

        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(markdown_output)
    except Exception as e:
        # Avoid crashing the background task
        print(f"Bridge error during update: {e}")


async def background_updater(app: TextualApp):
    """Periodically updates the state file in the background."""
    while True:
        update_state_file(app)
        await asyncio.sleep(0.5)


async def on_user_prompt_requested(app: TextualApp):
    global _updater_task
    if _updater_task is None:
        _updater_task = asyncio.create_task(background_updater(app))

    # The UI needs a moment to 'settle' and paint after the prompt is enabled.
    await asyncio.sleep(0.1)

    # Initial update for this prompt request
    update_state_file(app)

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("WAITING")

    print(f"Bridge: Waiting for input in {INPUT_FILE}...")

    while True:
        if INPUT_FILE.exists():
            content = INPUT_FILE.read_text(encoding="utf-8").strip()
            INPUT_FILE.unlink()

            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                f.write("PROCESSING")

            print(f"Bridge: Processing input: {content}")

            if content == "/exit":
                await app.action_quit()
                return

            app.user_input.submit_input(content)
            break

        await asyncio.sleep(0.2)


if __name__ == "__main__":
    setup_bridge()
    print("Bridge started. Waiting for app...")

    # We pass arguments via sys.argv if needed, but for now defaults are fine
    # To use stub: sys.argv.append("--stub")
    if "--stub" not in sys.argv:
        sys.argv.append("--stub")  # Default to stub for safety/testing

    try:
        asyncio.run(main_async(on_user_prompt_requested=on_user_prompt_requested))
    except Exception as e:
        print(f"Bridge error: {e}")
