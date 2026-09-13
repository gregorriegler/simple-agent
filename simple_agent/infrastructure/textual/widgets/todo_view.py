from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Markdown

from simple_agent.application.agent_id import AgentId
from simple_agent.application.intent import Intents
from simple_agent.application.todos import Todos


class TodoView(VerticalScroll):
    def __init__(
        self,
        agent_id: AgentId,
        intents: Intents,
        todos: Todos,
        markdown_id: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.agent_id = agent_id
        self.intents = intents
        self.todos = todos
        self.markdown_id = markdown_id
        self.content = ""
        self.load_content()

    def compose(self):
        yield Markdown(self.content, id=self.markdown_id)

    def load_content(self) -> str:
        intent = self.intents.read(self.agent_id)
        todos = self.todos.read(self.agent_id)
        sections = [f"**Intent:** {intent}" if intent else "", todos]
        self.content = "\n\n".join(section for section in sections if section)
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
