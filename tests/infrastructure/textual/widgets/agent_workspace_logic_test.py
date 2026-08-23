from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace


def create_workspace(agent_id: AgentId) -> AgentWorkspace:
    return AgentWorkspace(
        suggestion_provider=None,
        agent_id=agent_id,
        log_id="log-id",
        tool_results_id="tool-id",
    )


def test_shows_intent_above_todos(tmp_path):
    agent_id = AgentId("test_agent", root=tmp_path)
    agent_id.intent_filename().write_text("Ship the intent panel", encoding="utf-8")
    agent_id.todo_filename().write_text("- [ ] write a test", encoding="utf-8")

    workspace = create_workspace(agent_id)

    assert workspace.todo_view.content == (
        "**Intent:** Ship the intent panel\n\n- [ ] write a test"
    )


def test_panel_is_visible_when_only_intent_has_content(tmp_path):
    agent_id = AgentId("test_agent", root=tmp_path)
    agent_id.intent_filename().write_text("Ship the intent panel", encoding="utf-8")

    workspace = create_workspace(agent_id)

    assert workspace.todo_view.content == "**Intent:** Ship the intent panel"
    assert workspace.todo_view.styles.display != "none"


def test_refreshes_intent_on_tool_result(tmp_path):
    agent_id = AgentId("test_agent", root=tmp_path)
    workspace = create_workspace(agent_id)

    agent_id.intent_filename().write_text("A new goal", encoding="utf-8")
    workspace.refresh_todos()

    assert workspace.todo_view.content == "**Intent:** A new goal"
