import re

from textual.containers import VerticalScroll
from textual.widgets import Markdown


class ChatLog(VerticalScroll):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pending_messages = []

    def on_mount(self) -> None:
        if self._pending_messages:
            # Batch mount all historical messages for performance
            widgets = [Markdown(m.rstrip()) for m in self._pending_messages]
            self.mount(*widgets)
            self._pending_messages.clear()
            self.scroll_end(animate=False)

    def write(self, message: str) -> None:
        if not self.is_mounted:
            self._pending_messages.append(message)
            return
        self.mount(Markdown(message.rstrip()))
        self.scroll_end(animate=False)

    def add_user_message(self, text: str) -> None:
        display_text = text
        pattern = r'<file_context path="([^"]+)">.*?</file_context>'
        matches = list(re.finditer(pattern, display_text, flags=re.DOTALL))

        if matches:
            core_text = re.sub(pattern, "", display_text, flags=re.DOTALL).strip()
            attachments = []
            for match in matches:
                path = match.group(1)
                marker = f"[📦{path}]"
                if marker not in core_text:
                    attachments.append(marker)
            display_text = core_text
            if attachments:
                display_text += "\n" + "\n".join(attachments)

        self.write(f"**User:** {display_text}")

    def add_assistant_message(self, message: str, agent_name: str) -> None:
        self.write(f"**{agent_name}:** {message}")
