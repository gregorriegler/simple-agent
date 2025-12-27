from textual.containers import VerticalScroll
from textual.widgets import Markdown
from textual.css.query import NoMatches

class TodoView(VerticalScroll):
    def __init__(self, content: str, markdown_id: str, **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.markdown_id = markdown_id

    def compose(self):
        yield Markdown(self.content, id=self.markdown_id)

    def update(self, content: str) -> None:
        try:
            markdown = self.query_one(Markdown)
            markdown.update(content)
        except NoMatches:
            pass
