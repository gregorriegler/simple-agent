import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import SessionClearedEvent
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from simple_agent.infrastructure.textual.widgets.todo_view import TodoView
from tests.infrastructure.textual.test_utils import MockUserInput


@pytest.mark.asyncio
async def test_session_cleared_clears_todos():
    agent_id = AgentId("Agent")
    app = TextualApp(MockUserInput(), agent_id)

    async with app.run_test() as pilot:
        # Mock TodoView to have content
        todo_view = app.query_one(TodoView)
        todo_view.update("Some todos")
        assert todo_view.has_content

        # Trigger SessionClearedEvent
        app.on_domain_event_message(DomainEventMessage(SessionClearedEvent(agent_id)))
        await pilot.pause()

        # Verify content is cleared
        assert not todo_view.has_content

        # Verify visibility is hidden (via container)
        # We can check if the splitter is hidden or the view itself
        # TextualApp uses ResizableVertical.set_bottom_visibility
        # which sets styles.display

        # Accessing private attribute to verify state change if needed,
        # but checking styles is better.
        # ResizableVertical.set_bottom_visibility sets bottom_widget and splitter display.

        assert todo_view.styles.display == "none"
