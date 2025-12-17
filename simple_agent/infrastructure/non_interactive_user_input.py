from simple_agent.application.user_input import UserInput


class NonInteractiveUserInput(UserInput):

    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def close(self) -> None:
        pass
