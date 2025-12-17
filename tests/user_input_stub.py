from simple_agent.application.user_input import UserInput
from simple_agent.application.io import IO


class UserInputStub(UserInput):
    def __init__(self, io: IO):
        self.io = io

    #TODO do we still need this?
    def read(self) -> str:
        return self.io.input("").strip()

    async def read_async(self) -> str:
        return self.read()

    def escape_requested(self) -> bool:
        return self.io.escape_requested()

    def close(self) -> None:
        pass
