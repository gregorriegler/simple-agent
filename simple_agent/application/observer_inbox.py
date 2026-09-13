from .inbox import Inbox


class ObserverInbox(Inbox):
    """An observer's inbox: besides messages it holds the latest packet about the observed agent, read as a prompt."""

    def __init__(self):
        super().__init__()
        self._packet: str | None = None

    def observe(self, packet: str) -> None:
        self._packet = packet
        self._refresh()

    def take(self) -> str:
        if not self.is_empty() or self._packet is None:
            return super().take()
        packet, self._packet = self._packet, None
        self._refresh()
        return packet

    def _has_something(self) -> bool:
        return super()._has_something() or self._packet is not None
