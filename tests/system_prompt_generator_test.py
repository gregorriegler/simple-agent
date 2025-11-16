from pathlib import Path

import pytest
from approvaltests import verify

from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.ground_rules import GroundRules
from simple_agent.application.system_prompt import AgentPrompt
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.infrastructure.agent_library import (
    BuiltinAgentLibrary,
    FileSystemAgentLibrary,
)
from tests.test_helpers import create_all_tools_for_test


def test_generate_orchestrator_agent_system_prompt():
    tool_library = create_all_tools_for_test()
    verify_system_prompt("orchestrator", tool_library)


def test_generate_coding_system_prompt():
    tool_library = create_all_tools_for_test()
    verify_system_prompt("coding", tool_library)


def verify_system_prompt(agent_type, tool_library):
    agent_library = BuiltinAgentLibrary(GroundRulesStub())
    tools_documentation = generate_tools_documentation(tool_library.tools, agent_library.list_agent_types())
    prompt = agent_library.read_agent_definition(agent_type).load_prompt()
    system_prompt = prompt.render(tools_documentation)
    verify(system_prompt)


@pytest.mark.parametrize(
    ("agent_type", "definition_content", "expected_keys"),
    [
        (
            "sample",
            """---
name: Sample Agent
tools: write_todos,ls,cat
---

# Role
Content here""",
            ['write_todos', 'ls', 'cat'],
        ),
        (
            "list-sample",
            """---
name: Sample List Agent
tools:
- bash
- cat
---

# Role
Content here""",
            ['bash', 'cat'],
        ),
        (
            "no-keys",
            """---
description: Sample agent
---

# Role
Content here""",
            [],
        ),
        (
            "no-separator",
            """# Role
Content here""",
            [],
        ),
    ],
)
def test_extract_tool_keys_from_prompt(agent_type, definition_content, expected_keys, tmp_path: Path):
    agent_library = create_filesystem_agent_library(tmp_path)
    write_agent_definition(tmp_path, agent_type, definition_content)

    result = extract_tool_keys(agent_type, agent_library)

    assert result == expected_keys


def test_render_inserts_agents_content_with_placeholder():
    prompt = AgentPrompt(
        agent_name="Test",
        template="Header\n{{AGENTS.MD}}\n{{DYNAMIC_TOOLS_PLACEHOLDER}}\nFooter",
        tool_keys=[],
        agents_content="AGENTS CONTENT"
    )

    result = prompt.render("TOOLS DOCS")

    assert result == "Header\nAGENTS CONTENT\nTOOLS DOCS\nFooter"


def test_render_removes_placeholder_when_no_agents_content():
    prompt = AgentPrompt(
        agent_name="Test",
        template="Header\n{{AGENTS.MD}}\nFooter",
        tool_keys=[],
        agents_content=""
    )

    result = prompt.render("TOOLS DOCS")

    assert result == "Header\n\nFooter"


def extract_tool_keys(agent_type: str, agent_library: AgentLibrary) -> list[str]:
    prompt = agent_library.read_agent_definition(agent_type).load_prompt()
    return prompt.tool_keys


def create_filesystem_agent_library(directory: Path) -> FileSystemAgentLibrary:
    library = FileSystemAgentLibrary(str(directory))
    library.ground_rules = GroundRulesStub()
    return library


def write_agent_definition(directory: Path, agent_type: str, content: str) -> None:
    path = directory / f"{agent_type}.agent.md"
    path.write_text(content, encoding="utf-8")


class GroundRulesStub(GroundRules):

      def read(self) -> str:
          return "# Test AGENTS.md content\nThis is a stub for testing."
