import os
import sys
import threading
from difflib import SequenceMatcher
from pathlib import Path

import pytest
from rich.console import Console

from simple_agent.main import main


def fuzzy_verify(actual: str, approved_path: Path, threshold: float = 0.68):
    if not approved_path.exists():
        approved_path.parent.mkdir(parents=True, exist_ok=True)
        approved_path.write_text(actual, encoding="utf-8")
        pytest.fail(f"No approved file found. Created: {approved_path}\nReview and re-run.")

    approved = approved_path.read_text(encoding="utf-8")
    ratio = SequenceMatcher(None, actual, approved).ratio()

    if ratio < threshold:
        # Write received file for comparison
        received_path = approved_path.with_name(
            approved_path.name.replace(".approved.txt", ".received.txt")
        )
        received_path.write_text(actual, encoding="utf-8")
        pytest.fail(
            f"Fuzzy match failed: {ratio:.1%} similarity (threshold: {threshold:.0%})\n"
            f"Received: {received_path}\n"
            f"Approved: {approved_path}"
        )

@pytest.mark.flaky(reruns=3)
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
        async def do_capture():
            for _ in range(10):
                await app._pilot.pause()
            console = Console(record=True, width=80, force_terminal=False)
            console.print(app.screen._compositor)
            captured.append(console.export_text())
            capture_done.set()

        app.call_from_thread(do_capture)
        capture_done.wait(timeout=5.0)
        app.user_input.submit_input("")

    app = main(on_user_prompt_requested=unblock_agent)

    app.shutdown()

    approved_path = Path(__file__).parent / "approved_files" / "end_to_end_test.test_golden_master_agent_stub.approved.txt"
    fuzzy_verify(captured[0].replace("▃", "").replace("╸", ""), approved_path)
