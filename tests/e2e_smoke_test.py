import io
import os
import subprocess
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

import pytest
from rich.console import Console

from simple_agent.main import main_async


def fuzzy_verify(actual: str, approved_path: Path, threshold: float = 0.5):
    if not approved_path.exists():
        approved_path.parent.mkdir(parents=True, exist_ok=True)
        approved_path.write_text(actual, encoding="utf-8")
        pytest.fail(
            f"No approved file found. Created: {approved_path}\nReview and re-run."
        )

    approved = approved_path.read_text(encoding="utf-8")
    ratio = SequenceMatcher(None, actual, approved).ratio()

    if ratio < threshold:
        received_path = approved_path.with_name(
            approved_path.name.replace(".approved.txt", ".received.txt")
        )
        received_path.write_text(actual, encoding="utf-8")
        pytest.fail(
            f"Fuzzy match failed: {ratio:.1%} similarity (threshold: {threshold:.0%})\n"
            f"Received: {received_path}\n"
            f"Approved: {approved_path}"
        )


@pytest.mark.flaky(reruns=2, reruns_delay=0.5)
@pytest.mark.asyncio
async def test_golden_master_agent_stub(monkeypatch, tmp_path):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(tmp_path)
    monkeypatch.setenv("PYTHONPATH", project_root)

    monkeypatch.setattr(sys, "argv", ["main.py", "--stub", "Hello, world!"])

    approved_path = (
        Path(__file__).parent
        / "approved_files"
        / "e2e_smoke_test.test_golden_master_agent_stub.approved.txt"
    )

    def normalize(text):
        return text.replace("▃", "").replace("╸", "").replace("▂", "").replace("▄", "")

    captured = []

    async def on_user_prompt_requested(app):
        def get_screen_content():
            console = Console(
                record=True,
                width=80,
                force_terminal=False,
                file=io.StringIO(),
                legacy_windows=False,
                safe_box=False,
            )
            console.print(app.screen._compositor)
            return normalize(console.export_text())

        # Wait briefly for the main content to appear.
        max_wait_seconds = 0.5
        poll_interval = 0.02
        start_time = time.monotonic()

        while time.monotonic() - start_time < max_wait_seconds:
            await app._pilot.pause(poll_interval)
            content = get_screen_content()

            if "complete-task" in content:
                break

        captured.append(get_screen_content())
        app.user_input.submit_input(app._root_agent_id, "")

    await main_async(on_user_prompt_requested=on_user_prompt_requested)

    fuzzy_verify(captured[0].replace("▃", "").replace("╸", ""), approved_path)


def test_non_interactive_stub_exits_successfully(tmp_path):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "simple_agent.main",
            "--stub",
            "--non-interactive",
            "Hello, world!",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stdout + result.stderr
