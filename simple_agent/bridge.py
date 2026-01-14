#!/usr/bin/env python
import asyncio
import json
import os
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
STATE_FILE = OUTBOX / "state.json"


def setup_bridge():
    if BRIDGE_DIR.exists():
        import shutil

        shutil.rmtree(BRIDGE_DIR)
    BRIDGE_DIR.mkdir()
    INBOX.mkdir()
    OUTBOX.mkdir()


def get_screen_content(app: TextualApp) -> str:
    console = Console(
        record=True,
        width=120,
        height=40,
        force_terminal=False,
        file=open(os.devnull, "w"),
        legacy_windows=False,
        safe_box=False,
    )
    # Render the screen to the console
    console.print(app.screen._compositor)
    return console.export_text()


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
                    entry = {"title": str(collapsible.title), "content": "", "collapsed": collapsible.collapsed}
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


async def on_user_prompt_requested(app: TextualApp):
    # Stabilize screen
    await app._pilot.pause(0.5)

    screen_content = get_screen_content(app)
    structured_data = get_structured_state(app)

    state = {
        "screen": screen_content,
        "data": structured_data,
        "timestamp": time.time(),
    }

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

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

        await asyncio.sleep(0.1)


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
