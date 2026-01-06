from pathlib import Path

import pytest

from simple_agent.application.agent_id import AgentId, AgentIdSuffixer


def test_agent_id_requires_non_empty_input():
    for invalid in ["", " ", "   "]:
        with pytest.raises(ValueError):
            AgentId(invalid)


def test_with_suffix_adds_suffix_and_returns_self_for_empty_suffix():
    base = AgentId("root")

    suffixed = base.with_suffix("-1")

    assert suffixed == AgentId("root-1")
    assert base.raw == "root"
    assert base.with_suffix("") is base


def test_create_subagent_id_uses_suffixer_counts_per_base():
    base = AgentId("parent")
    suffixer = AgentIdSuffixer()

    first_child = base.create_subagent_id("child", suffixer)
    second_child = base.create_subagent_id("child", suffixer)
    first_other_child = base.create_subagent_id("other", suffixer)

    assert first_child == AgentId("parent/child")
    assert second_child == AgentId("parent/child-2")
    assert first_other_child == AgentId("parent/other")


def test_parent_and_depth_navigation():
    root = AgentId("root")
    nested = AgentId("root/child/grandchild")

    assert not root.has_parent()
    assert root.parent() is None
    assert nested.has_parent()
    parent = nested.parent()
    assert parent == AgentId("root/child")
    assert parent is not None
    assert parent.parent() == AgentId("root")
    assert nested.depth() == 2


def test_filesystem_and_repr_helpers():
    agent_id = AgentId(r"root/sub agent\\id")

    assert agent_id.for_filesystem() == "root-sub-agent--id"
    expected_filename = Path(".") / ".root-sub-agent--id.todos.md"
    assert agent_id.todo_filename() == expected_filename
    assert agent_id.for_ui() == "root-sub-agent--id"
    assert str(agent_id) == agent_id.raw
    assert repr(agent_id) == f"AgentId('{agent_id.raw}')"
    assert len({AgentId("dup"), AgentId("dup")}) == 1
