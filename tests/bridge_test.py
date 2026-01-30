import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual import events

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import bridge  # noqa: E402


@pytest.mark.asyncio
async def test_process_input_normal_text(tmp_path):
    input_file = tmp_path / "message.txt"
    input_file.write_text("hello world", encoding="utf-8")

    with patch("bridge.INPUT_FILE", input_file):
        app = MagicMock()
        app.user_input = MagicMock()
        app.user_input.submit_input = MagicMock()

        await bridge.process_input(app)

        app.user_input.submit_input.assert_called_with("hello world")


@pytest.mark.asyncio
async def test_process_input_exit(tmp_path):
    input_file = tmp_path / "message.txt"
    input_file.write_text("/exit", encoding="utf-8")

    with patch("bridge.INPUT_FILE", input_file):
        app = MagicMock()
        app.action_quit = AsyncMock()

        await bridge.process_input(app)

        app.action_quit.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_input_key_injection(tmp_path):
    input_file = tmp_path / "message.txt"
    input_file.write_text("/key alt+left", encoding="utf-8")

    with patch("bridge.INPUT_FILE", input_file):
        app = MagicMock()
        app.post_message = MagicMock()
        app.user_input = (
            MagicMock()
        )  # Mock to prevent AttributeError if logic falls through

        await bridge.process_input(app)

        # This assertion verifies that the /key command logic is implemented
        assert app.post_message.called, (
            "app.post_message should be called for /key command"
        )
        call_args = app.post_message.call_args
        event = call_args[0][0]
        assert isinstance(event, events.Key)
        assert event.key == "alt+left"
