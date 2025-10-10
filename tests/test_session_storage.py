from simple_agent.application.llm import Messages


class SessionStorageStub:
    def __init__(self):
        self.saved = "None"

    def load(self):
        return Messages()

    def save(self, messages):
        self.saved = "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)
