from textual.containers import VerticalScroll
from textual.widgets import Markdown
import re


class ChatLog(VerticalScroll):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pending_messages = []

    def on_mount(self) -> None:
        if self._pending_messages:
            for message in self._pending_messages:
                self.mount(Markdown(message.rstrip()))
            self._pending_messages.clear()
            self.scroll_end(animate=False)

    def write(self, message: str) -> None:
        if not self.is_mounted:
            self._pending_messages.append(message)
            return
        self.mount(Markdown(message.rstrip()))
        self.scroll_end(animate=False)

    def add_user_message(self, text: str) -> None:
        """
        Add a user message to the log, handling file context display.
        """
        # Compact file context for display
        display_text = text

        # Find all context blocks
        pattern = r'<file_context path="([^"]+)">.*?</file_context>'
        matches = list(re.finditer(pattern, display_text, flags=re.DOTALL))

        if matches:
            # Remove all blocks from the text first to get the core message
            core_text = re.sub(pattern, "", display_text, flags=re.DOTALL).strip()

            attachments = []
            for match in matches:
                path = match.group(1)
                marker = f"[📦{path}]"

                # If the marker is already in core_text, we don't need to do anything else for this file
                if marker in core_text:
                    continue

                # Fallback for manually typed paths or older logic
                escaped_path = re.escape(path)
                if re.search(escaped_path, core_text):
                    # Replace the first occurrence of the path with the marker
                    core_text = re.sub(escaped_path, marker, core_text, count=1)
                else:
                    attachments.append(marker)

            display_text = core_text
            if attachments:
                display_text += "\n" + "\n".join(attachments)

        self.write(f"**User:** {display_text}")

    def add_assistant_message(self, message: str, agent_name: str) -> None:
        """
        Add an assistant message to the log.
        """
        self.write(f"**{agent_name}:** {message}")
