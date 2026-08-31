import io

import pytest
from rich.console import Console
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Static, TextArea

from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.widgets.tool_log import (
    THOUGHT_EMOJI,
    CollapsedToolEntry,
    ToolCollapsible,
    _format_tool_title,
    _tool_emoji_for,
)
from tests.infrastructure.textual.test_utils import eventually

SHORT = "cat simple_agent/main.py"
LONG = (
    "bash rg 'a fairly long search pattern that will certainly wrap across lines' "
    "-g '*.py' --hidden"
)
SCREEN = (64, 14)


def title_of(message: str) -> str:
    return _format_tool_title(message, _tool_emoji_for(message))


def a_result(
    body: str = "hello", status: ToolResultStatus = ToolResultStatus.SUCCESS
) -> SingleToolResult:
    return SingleToolResult(message=body, status=status)


def a_collapsible(
    message: str, status_class: str = "tool-status-success"
) -> ToolCollapsible:
    text_area = TextArea("hello", read_only=True, show_cursor=False)
    text_area.styles.height = 3
    return ToolCollapsible(
        text_area,
        title=title_of(message),
        collapsed=True,
        classes=status_class,
    )


class EntryApp(App):
    CSS = TextualApp.CSS

    def __init__(self, widgets):
        super().__init__()
        self._widgets = widgets

    def compose(self) -> ComposeResult:
        yield from self._widgets


async def rendered(widgets, hover: bool = False, focus: bool = False) -> list[str]:
    app = EntryApp(widgets)
    async with app.run_test(size=SCREEN) as pilot:
        app.screen.set_focus(None)
        await pilot.pause()
        await pilot.pause()
        if focus:
            app.screen.focus_next()
            await pilot.pause()
        if hover:
            await pilot.hover(None, offset=(4, 0))
            await pilot.pause()
        console = Console(
            record=True,
            width=SCREEN[0],
            file=io.StringIO(),
            color_system="truecolor",
            legacy_windows=False,
        )
        console.print(app.screen._compositor)
        text = console.export_text(styles=True)
    return [line for line in text.splitlines() if line.strip()]


@pytest.mark.asyncio
async def test_a_collapsed_entry_builds_no_text_area():
    app = EntryApp([CollapsedToolEntry.of_result(title_of(SHORT), a_result())])
    async with app.run_test():
        assert not app.query(TextArea)


@pytest.mark.asyncio
async def test_a_collapsed_entry_renders_like_a_collapsed_collapsible():
    real = await rendered([a_collapsible(SHORT), a_collapsible(LONG)])
    imitation = await rendered(
        [
            CollapsedToolEntry.of_result(title_of(SHORT), a_result()),
            CollapsedToolEntry.of_result(title_of(LONG), a_result()),
        ]
    )

    assert imitation == real


@pytest.mark.asyncio
async def test_clicking_an_entry_turns_it_into_an_expanded_collapsible():
    entry = CollapsedToolEntry.of_result(title_of(SHORT), a_result("the output"))
    app = EntryApp([a_collapsible(SHORT), entry, a_collapsible(LONG)])
    async with app.run_test(size=SCREEN) as pilot:
        await pilot.click(CollapsedToolEntry)
        await eventually(
            pilot,
            lambda: not app.query(CollapsedToolEntry),
            "the entry to be replaced",
        )

        kinds = [type(child).__name__ for child in app.screen.children]
        assert kinds == ["ToolCollapsible", "ToolCollapsible", "ToolCollapsible"]

        upgraded = app.screen.children[1]
        assert not upgraded.collapsed
        assert upgraded.title == title_of(SHORT)
        assert upgraded.query_one(TextArea).text == "the output"


def a_thought_collapsible() -> ToolCollapsible:
    return ToolCollapsible(
        Static(Text("thinking it over"), classes="thought"),
        title=f"{THOUGHT_EMOJI} thought",
        collapsed=True,
        classes="thought",
    )


@pytest.mark.asyncio
async def test_a_collapsed_thought_renders_like_a_collapsed_collapsible():
    real = await rendered([a_thought_collapsible()])
    imitation = await rendered(
        [CollapsedToolEntry.of_thought(f"{THOUGHT_EMOJI} thought", "thinking it over")]
    )

    assert imitation == real


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, status_class",
    [
        (ToolResultStatus.SUCCESS, "tool-status-success"),
        (ToolResultStatus.FAILURE, "tool-status-error"),
        (ToolResultStatus.CANCELLED, "tool-status-cancelled"),
    ],
)
async def test_every_status_renders_like_its_collapsible(status, status_class):
    real = await rendered([a_collapsible(SHORT, status_class)])
    imitation = await rendered(
        [CollapsedToolEntry.of_result(title_of(SHORT), a_result(status=status))]
    )

    assert imitation == real


@pytest.mark.asyncio
async def test_a_hovered_entry_renders_like_a_hovered_collapsible():
    real = await rendered([a_collapsible(SHORT)], hover=True)
    imitation = await rendered(
        [CollapsedToolEntry.of_result(title_of(SHORT), a_result())], hover=True
    )

    assert imitation == real


@pytest.mark.asyncio
async def test_a_focused_entry_renders_like_a_focused_collapsible():
    real = await rendered([a_collapsible(SHORT)], focus=True)
    imitation = await rendered(
        [CollapsedToolEntry.of_result(title_of(SHORT), a_result())], focus=True
    )

    assert imitation == real


@pytest.mark.asyncio
async def test_enter_opens_a_focused_entry():
    entry = CollapsedToolEntry.of_result(title_of(SHORT), a_result("the output"))
    app = EntryApp([entry])
    async with app.run_test(size=SCREEN) as pilot:
        app.screen.focus_next()
        await pilot.pause()
        assert app.focused is entry

        await pilot.press("enter")
        await eventually(
            pilot,
            lambda: not app.query(CollapsedToolEntry),
            "enter to open the entry",
        )

        assert app.query_one(TextArea).text == "the output"


@pytest.mark.asyncio
async def test_opening_an_entry_moves_the_focus_onto_it():
    entries = [
        CollapsedToolEntry.of_result(title_of(f"cat file{i}.py"), a_result())
        for i in range(3)
    ]
    app = EntryApp(entries)
    async with app.run_test(size=SCREEN) as pilot:
        entries[1].focus()
        await pilot.pause()

        upgraded = entries[1].upgrade()
        await eventually(
            pilot,
            lambda: not app.query(CollapsedToolEntry).filter("#none")
            and upgraded.is_mounted,
            "the entry to be replaced",
        )
        await eventually(
            pilot,
            lambda: app.focused is not None and app.focused in upgraded.walk_children(),
            "the focus to land on the opened collapsible",
        )


@pytest.mark.asyncio
async def test_clicking_an_entry_moves_the_focus_onto_it():
    entries = [
        CollapsedToolEntry.of_result(title_of(f"cat file{i}.py"), a_result())
        for i in range(3)
    ]
    app = EntryApp(entries)
    async with app.run_test(size=SCREEN) as pilot:
        await pilot.pause()
        await pilot.click(CollapsedToolEntry, offset=(4, 1))

        await eventually(
            pilot,
            lambda: len(app.query(CollapsedToolEntry)) == 2,
            "the clicked entry to open",
        )

        opened = app.query_one(ToolCollapsible)
        await eventually(
            pilot,
            lambda: app.focused is not None and app.focused in opened.walk_children(),
            "the focus to land on the clicked collapsible",
        )
