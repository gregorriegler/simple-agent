from abc import ABC, abstractmethod


class SlashCommand(ABC):
    @abstractmethod
    async def accept(self, visitor: "SlashCommandVisitor") -> None:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass


class ClearCommand(SlashCommand):
    @property
    def name(self) -> str:
        return "/clear"

    @property
    def description(self) -> str:
        return "Clear conversation history"

    async def accept(self, visitor: "SlashCommandVisitor") -> None:
        await visitor.clear_conversation(self)


class ModelCommand(SlashCommand):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @property
    def name(self) -> str:
        return "/model"

    @property
    def description(self) -> str:
        return "Change model"

    async def accept(self, visitor: "SlashCommandVisitor") -> None:
        await visitor.change_model(self)


class AgentCommand(SlashCommand):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    @property
    def name(self) -> str:
        return "/agent"

    @property
    def description(self) -> str:
        return "Change agent"

    async def accept(self, visitor: "SlashCommandVisitor") -> None:
        visit_agent_command = getattr(visitor, "visit_agent_command", None)
        if visit_agent_command is None:
            raise NotImplementedError("Agent command handling is not implemented")
        await visit_agent_command(self)


class SlashCommandVisitor(ABC):
    @abstractmethod
    async def clear_conversation(self, command: ClearCommand) -> None:
        pass

    @abstractmethod
    async def change_model(self, command: ModelCommand) -> None:
        pass
