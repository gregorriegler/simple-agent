from textual.containers import VerticalScroll
from textual.widgets import Markdown

class ChatLog(VerticalScroll):
    def write(self, message: str) -> None:
        self.mount(Markdown(message.rstrip()))
        self.scroll_end(animate=False)
