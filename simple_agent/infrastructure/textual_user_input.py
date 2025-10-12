from queue import Queue, Empty

from simple_agent.application.user_input import UserInput


class TextualUserInput(UserInput):

    def __init__(self):
        self.input_queue: Queue[str] = Queue()
        self.escape_flag = False
        self.closing = False

    def read(self) -> str:
        while not self.closing:
            try:
                return self.input_queue.get(timeout=0.1)
            except Empty:
                continue
        return ""

    def submit_input(self, message: str):
        self.escape_flag = False
        self.input_queue.put(message)

    def escape_requested(self) -> bool:
        return self.escape_flag

    def request_escape(self):
        self.escape_flag = True

    def close(self):
        self.closing = True
