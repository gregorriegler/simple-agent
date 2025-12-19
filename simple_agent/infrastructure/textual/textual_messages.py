from textual.message import Message

class DomainEventMessage(Message):
    def __init__(self, event) -> None:
        super().__init__()
        self.event = event
