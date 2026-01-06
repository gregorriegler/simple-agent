from textual.containers import VerticalScroll
from textual.widgets import Markdown
from textual.css.query import NoMatches
from simple_agent.application.agent_id import AgentId
from pathlib import Path


class TodoView(VerticalScroll):
    def __init__(self, agent_id: AgentId, markdown_id: str, **kwargs):
        super().__init__(**kwargs)
        self.agent_id = agent_id
        self.markdown_id = markdown_id
        self.content = ""
        self.load_content()

    def compose(self):
        yield Markdown(self.content, id=self.markdown_id)

    def load_content(self) -> str:
        path = Path(self.agent_id.todo_filename())
        if not path.exists():
            self.content = ""
        else:
            self.content = path.read_text(encoding="utf-8").strip()
        return self.content

    def refresh_content(self) -> None:
        content = self.load_content()
        try:
            markdown = self.query_one(Markdown)
            markdown.update(content)
        except NoMatches:
            pass

    def update(self, content: str) -> None:
        """Manually update the content of the TodoView (e.g. to clear it)."""
        self.content = content
        try:
            markdown = self.query_one(Markdown)
            markdown.update(content)
        except NoMatches:
            pass

    @property
    def has_content(self) -> bool:
        return bool(self.content)
