import pytest

from simple_agent.application.slash_commands import (
    ClearCommand,
    ModelCommand,
    SlashCommandVisitor,
)

pytestmark = pytest.mark.asyncio


class TestSlashCommandVisitor(SlashCommandVisitor):
    """Test visitor that records which methods were called."""

    def __init__(self):
        self.cleared = False
        self.model_changed_to = None

    async def clear_conversation(self, command: ClearCommand) -> None:
        self.cleared = True

    async def change_model(self, command: ModelCommand) -> None:
        self.model_changed_to = command.model_name


async def test_clear_command_accepts_visitor():
    visitor = TestSlashCommandVisitor()
    command = ClearCommand()

    await command.accept(visitor)

    assert visitor.cleared is True


async def test_model_command_accepts_visitor():
    visitor = TestSlashCommandVisitor()
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
