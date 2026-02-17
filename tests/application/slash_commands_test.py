import pytest

from simple_agent.application.slash_commands import (
    AgentCommand,
    ClearCommand,
    ModelCommand,
    SlashCommandVisitor,
)

class SlashCommandVisitorSpy(SlashCommandVisitor):
    """Test visitor that records which methods were called."""

    def __init__(self):
        self.cleared = False
        self.model_changed_to = None

    async def clear_conversation(self, command: ClearCommand) -> None:
        self.cleared = True

    async def change_model(self, command: ModelCommand) -> None:
        self.model_changed_to = command.model_name

    async def visit_agent_command(self, command: AgentCommand) -> None:
        return None


async def test_clear_command_accepts_visitor():
    visitor = SlashCommandVisitorSpy()
    command = ClearCommand()

    await command.accept(visitor)

    assert visitor.cleared is True


async def test_model_command_accepts_visitor():
    visitor = SlashCommandVisitorSpy()
    command = ModelCommand("gpt-4")

    await command.accept(visitor)

    assert visitor.model_changed_to == "gpt-4"


def test_clear_command_has_name_and_description():
    command = ClearCommand()
    assert command.name == "/clear"
    assert command.description == "Clear conversation history"


def test_model_command_has_name_and_description():
    command = ModelCommand("gpt-4")
    assert command.name == "/model"
    assert command.description == "Change model"


def test_slash_command_visitor_requires_agent_handler():
    class IncompleteVisitor(SlashCommandVisitor):
        async def clear_conversation(self, command: ClearCommand) -> None:
            return None

        async def change_model(self, command: ModelCommand) -> None:
            return None

    with pytest.raises(TypeError):
        IncompleteVisitor()
