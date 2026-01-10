import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    UserPromptedEvent,
)
from simple_agent.application.llm import Messages
from simple_agent.application.session_storage import AgentMetadata
from simple_agent.infrastructure.file_session_storage import FileSessionStorage
from tests.session_test_bed import SessionTestBed


@pytest.mark.asyncio
async def test_continuing_session_replays_user_messages_as_events(tmp_path):
    """When continuing a session, previously sent user messages should be replayed as UserPromptedEvents."""
    agent_id = AgentId("Agent")
    storage = FileSessionStorage.create(tmp_path, continue_session=False, cwd=tmp_path)
    storage.save_messages(
        agent_id,
        Messages(
            [
                {"role": "user", "content": "Hello from the past"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        ),
    )

    continued_storage = FileSessionStorage.create(
        tmp_path, continue_session=True, cwd=tmp_path
    )

    result = await (
        SessionTestBed()
        .with_session_storage(continued_storage)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue please")
        .run()
    )

    # The historical user message should be replayed as an event
    result.assert_event_occured(
        UserPromptedEvent(agent_id=agent_id, input_text="Hello from the past")
    )


@pytest.mark.asyncio
async def test_continuing_session_replays_assistant_messages_as_events(tmp_path):
    """When continuing a session, previous assistant messages should be replayed as AssistantSaidEvents."""
    agent_id = AgentId("Agent")
    storage = FileSessionStorage.create(tmp_path, continue_session=False, cwd=tmp_path)
    storage.save_messages(
        agent_id,
        Messages(
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Previous response from assistant"},
            ]
        ),
    )

    continued_storage = FileSessionStorage.create(
        tmp_path, continue_session=True, cwd=tmp_path
    )

    result = await (
        SessionTestBed()
        .with_session_storage(continued_storage)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue")
        .run()
    )

    # The historical assistant message should be replayed as an event
    result.assert_event_occured(
        AssistantSaidEvent(
            agent_id=agent_id, message="Previous response from assistant"
        )
    )


@pytest.mark.asyncio
async def test_continuing_session_replays_subagent_history(tmp_path):
    """When continuing a session with subagents, their history should also be replayed."""
    parent_id = AgentId("Agent")
    subagent_id = AgentId("Agent/Coding")

    storage = FileSessionStorage.create(tmp_path, continue_session=False, cwd=tmp_path)
    storage.save_messages(
        parent_id,
        Messages(
            [
                {"role": "user", "content": "Parent task"},
                {
                    "role": "assistant",
                    "content": "Starting subagent\n🛠️[subagent coding Do the task /]",
                },
                {
                    "role": "user",
                    "content": "Result of 🛠️ subagent coding Do the task\nDone",
                },
            ]
        ),
    )
    storage.save_messages(
        subagent_id,
        Messages(
            [
                {"role": "user", "content": "Subagent task"},
                {"role": "assistant", "content": "Subagent response"},
            ]
        ),
    )

    continued_storage = FileSessionStorage.create(
        tmp_path, continue_session=True, cwd=tmp_path
    )

    result = await (
        SessionTestBed()
        .with_session_storage(continued_storage)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue")
        .run()
    )

    # Subagent should be started (tab created)
    result.assert_event_occured(
        AgentStartedEvent(agent_id=subagent_id, agent_name="Coding")
    )
    # Subagent's historical messages should be replayed
    result.assert_event_occured(
        UserPromptedEvent(agent_id=subagent_id, input_text="Subagent task")
    )
    result.assert_event_occured(
        AssistantSaidEvent(agent_id=subagent_id, message="Subagent response")
    )


@pytest.mark.asyncio
async def test_subagent_restoration_follows_message_stream_order(tmp_path):
    """Subagents should be restored when their tool call appears in the parent's message stream.

    This test verifies that subagent restoration happens via parsing tool calls in the
    message stream, not by scanning the filesystem. The correct order should be:
    1. Parent message with subagent tool call
    2. AgentStartedEvent for subagent
    3. Subagent messages
    4. Back to parent
    """
    parent_id = AgentId("Agent")
    subagent_id = AgentId("Agent/Coding")

    storage = FileSessionStorage.create(tmp_path, continue_session=False, cwd=tmp_path)
    storage.save_messages(
        parent_id,
        Messages(
            [
                {"role": "user", "content": "Build a feature"},
                {
                    "role": "assistant",
                    "content": "I'll delegate this.\n🛠️[subagent coding Implement the feature /]",
                },
                {
                    "role": "user",
                    "content": "Result of 🛠️ subagent coding Implement the feature\nFeature completed",
                },
                {"role": "assistant", "content": "The feature is done."},
            ]
        ),
    )
    storage.save_messages(
        subagent_id,
        Messages(
            [
                {"role": "user", "content": "Implement the feature"},
                {
                    "role": "assistant",
                    "content": "🛠️[complete-task Feature completed /]",
                },
            ]
        ),
    )

    continued_storage = FileSessionStorage.create(
        tmp_path, continue_session=True, cwd=tmp_path
    )

    result = await (
        SessionTestBed()
        .with_session_storage(continued_storage)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue")
        .run()
    )

    events = result.events.get_all_events()

    # Find the indices of key events
    parent_delegate_msg_idx = None
    subagent_started_idx = None
    subagent_msg_idx = None
    parent_done_msg_idx = None

    for i, event in enumerate(events):
        event_name = type(event).__name__
        agent_id = getattr(event, "agent_id", None)
        msg = getattr(event, "message", "")

        if event_name == "AssistantSaidEvent" and agent_id == parent_id:
            if "delegate" in msg:
                parent_delegate_msg_idx = i
            elif "done" in msg.lower():
                parent_done_msg_idx = i
        elif event_name == "AgentStartedEvent" and agent_id == subagent_id:
            subagent_started_idx = i
        elif event_name == "AssistantSaidEvent" and agent_id == subagent_id:
            subagent_msg_idx = i

    assert parent_delegate_msg_idx is not None, "Parent's delegate message not found"
    assert subagent_started_idx is not None, "Subagent started event not found"
    assert subagent_msg_idx is not None, "Subagent message not found"
    assert parent_done_msg_idx is not None, "Parent's done message not found"

    # The correct order should be:
    # parent_delegate_msg -> subagent_started -> subagent_msg -> parent_done_msg
    assert parent_delegate_msg_idx < subagent_started_idx, (
        f"Subagent should start after parent's delegate message. Got: delegate={parent_delegate_msg_idx}, started={subagent_started_idx}"
    )
    assert subagent_started_idx < subagent_msg_idx, (
        f"Subagent messages should come after subagent started. Got: started={subagent_started_idx}, msg={subagent_msg_idx}"
    )
    assert subagent_msg_idx < parent_done_msg_idx, (
        f"Parent's done message should come after subagent completes. Got: subagent_msg={subagent_msg_idx}, parent_done={parent_done_msg_idx}"
    )


@pytest.mark.asyncio
async def test_orphan_subagent_not_restored_without_tool_call(tmp_path):
    """Subagents that exist on disk but have no corresponding tool call should not be restored.

    This tests the scenario where a subagent folder exists (perhaps from a crashed session)
    but the parent's message history doesn't contain the tool call that created it.
    """
    parent_id = AgentId("Agent")
    orphan_subagent_id = AgentId("Agent/Orphan")

    storage = FileSessionStorage.create(tmp_path, continue_session=False, cwd=tmp_path)
    # Parent has no subagent tool calls
    storage.save_messages(
        parent_id,
        Messages(
            [
                {"role": "user", "content": "Do something"},
                {"role": "assistant", "content": "I'll do it directly."},
            ]
        ),
    )
    # But there's an orphan subagent folder on disk
    storage.save_messages(
        orphan_subagent_id,
        Messages(
            [
                {"role": "user", "content": "Orphan task"},
                {"role": "assistant", "content": "Orphan response"},
            ]
        ),
    )

    continued_storage = FileSessionStorage.create(
        tmp_path, continue_session=True, cwd=tmp_path
    )

    result = await (
        SessionTestBed()
        .with_session_storage(continued_storage)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue")
        .run()
    )

    # The orphan subagent should NOT be restored since there's no tool call for it
    events = result.events.get_all_events()
    orphan_started_events = [
        e
        for e in events
        if type(e).__name__ == "AgentStartedEvent"
        and getattr(e, "agent_id", None) == orphan_subagent_id
    ]

    assert len(orphan_started_events) == 0, (
        f"Orphan subagent should not be restored, but found {len(orphan_started_events)} AgentStartedEvent(s)"
    )


@pytest.mark.asyncio
async def test_continuing_session_restores_token_metadata(tmp_path):
    """When continuing a session, token usage metadata should be restored."""
    agent_id = AgentId("Agent")
    storage = FileSessionStorage.create(tmp_path, continue_session=False, cwd=tmp_path)
    storage.save_messages(
        agent_id,
        Messages(
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        ),
    )
    storage.save_metadata(
        agent_id,
        AgentMetadata(model="claude-3-sonnet", max_tokens=200000, input_tokens=1500),
    )

    continued_storage = FileSessionStorage.create(
        tmp_path, continue_session=True, cwd=tmp_path
    )

    result = await (
        SessionTestBed()
        .with_session_storage(continued_storage)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue")
        .run()
    )

    # Token metadata should be restored via AssistantRespondedEvent
    result.assert_event_occured(
        AssistantRespondedEvent(
            agent_id=agent_id,
            model="claude-3-sonnet",
            max_tokens=200000,
            input_tokens=1500,
        )
    )
