from simple_agent.application.user_input import UserInput
from simple_agent.application.io import IO


class UserInputStub(UserInput):
    def __init__(self, io: IO):
        self.io = io

    async def read_async(self) -> str:
        return self.io.input("").strip()

    def escape_requested(self) -> bool:
        return self.io.escape_requested()

    def close(self) -> None:
        pass
