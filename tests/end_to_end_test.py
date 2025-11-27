import os
import sys
import threading

import pytest
from approvaltests import verify
from rich.console import Console

from simple_agent.main import main

@pytest.mark.skip(reason="no way of currently testing this")
def test_golden_master_agent_stub(monkeypatch):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--test",
        "--stub",
        "Hello, world!"
    ])

    captured = []
    capture_done = threading.Event()

    def unblock_agent(app):
        # Capture screen from Textual's thread context
        async def do_capture():
            # Wait for UI to stabilize
            await app._pilot.pause()
            console = Console(record=True, width=80, force_terminal=False)
            console.print(app.screen._compositor)
            captured.append(console.export_text())
            capture_done.set()

        # Schedule capture on Textual's thread, then unblock
        app.call_from_thread(do_capture)
        capture_done.wait(timeout=5.0)
        app.user_input.submit_input("")

    app = main(on_user_prompt_requested=unblock_agent)

    app.shutdown()

    verify(captured[0])
