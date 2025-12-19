import asyncio

import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.textual.textual_app import TextualApp


class StubUserInput:
    def __init__(self) -> None:
        self.closed = False

    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_action_quit_cancels_session_task():
    cancelled = asyncio.Event()

    async def session_runner():
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    user_input = StubUserInput()
    app = TextualApp(user_input, AgentId("Agent"))
    app._session_runner = session_runner

    async with app.run_test() as pilot:
        app._pilot = pilot
        await pilot.pause()
        session_task = app._session_task
        assert session_task is not None

        app.action_quit()
        await asyncio.sleep(0)

        assert cancelled.is_set()
        assert user_input.closed
