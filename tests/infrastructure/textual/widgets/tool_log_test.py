from approvaltests import verify
from textual.app import App
from textual.widgets import Markdown

from simple_agent.application.tool_results import SingleToolResult
from simple_agent.infrastructure.textual.widgets.tool_log import (
    LIVE_ENTRY_WINDOW,
    ToolLog,
)
from tests.infrastructure.textual.test_utils import eventually


async def test_a_new_tool_call_keeps_a_collapsible_the_user_opened(ui):
    ui.call("first")
    ui.call("second")
    await ui.click("first")
    ui.call("third")

    verify(await ui.outline())


async def test_a_running_tool_call(ui):
    ui.call("bash sleep 3")

    verify(await ui.outline())


async def test_a_succeeded_tool_call(ui):
    ui.call("bash sleep 3")
    ui.succeed("bash sleep 3")

    verify(await ui.outline())


async def test_a_failed_tool_call(ui):
    ui.call("cat missing.txt")
    ui.fail("cat missing.txt", "No such file")

    verify(await ui.outline())


async def test_a_cancelled_tool_call(ui):
    ui.call("bash sleep 10")
    ui.cancel("bash sleep 10")

    verify(await ui.outline())
    body = await ui.body("bash sleep 10")
    assert body.has_class("tool-result-cancelled")
    assert not body.has_class("tool-result-error")


async def test_each_tool_gets_its_emoji(ui):
    ui.call("bash some args")
    ui.call("cat some args")
    ui.call("ls some args")
    ui.call("create-file some args")
    ui.call("replace-file-content some args")
    ui.call("subagent some args")
    ui.call("complete-task some args")
    ui.call("search_files some args")

    verify(await ui.outline())


async def test_a_result_title_replaces_the_call_title(ui):
    ui.call("search_files query=test")
    ui.finish("search_files query=test", SingleToolResult(display_title="Results"))

    verify(await ui.outline())


LONG_COMMAND = (
    "bash sleep 3 && echo 'this is a very long command with lots of arguments "
    "and options that will wrap to multiple lines'"
)


async def test_a_long_title_wraps_with_a_hanging_indent(ui):
    ui.call(LONG_COMMAND)

    verify(await ui.wrapped_title(LONG_COMMAND))


async def test_a_long_title_wraps_when_mounted_into_a_laid_out_log(ui):
    await ui.lay_out()
    ui.call(LONG_COMMAND)

    verify(await ui.wrapped_title(LONG_COMMAND))


async def test_replayed_tool_calls_become_cheap_entries(ui):
    ui.begin_replay()
    ui.call("bash echo hi")
    ui.succeed("bash echo hi")
    ui.end_replay()

    verify(await ui.outline())


async def test_a_replayed_call_without_a_result_stays_a_collapsible(ui):
    ui.begin_replay()
    ui.call("bash sleep 3")
    ui.end_replay()

    verify(await ui.outline())


async def test_live_tool_calls_still_build_a_collapsible(ui):
    ui.call("bash echo hi")
    ui.succeed("bash echo hi")

    verify(await ui.outline())


async def test_a_replayed_cancellation_keeps_its_status_and_place(ui):
    ui.begin_replay()
    ui.call("bash echo first")
    ui.succeed("bash echo first")
    ui.call("bash sleep 10")
    ui.cancel("bash sleep 10")
    ui.call("bash echo third")
    ui.succeed("bash echo third")
    ui.end_replay()

    verify(await ui.outline())


async def test_replayed_thoughts_keep_their_place_between_tool_calls(ui):
    ui.begin_replay()
    ui.call("bash echo first")
    ui.succeed("bash echo first")
    ui.think("thinking it over")
    ui.call("bash echo second")
    ui.succeed("bash echo second")
    ui.end_replay()

    verify(await ui.outline())


async def test_only_the_most_recent_entries_stay_collapsibles(ui):
    for i in range(LIVE_ENTRY_WINDOW + 3):
        ui.run(f"bash echo {i}")

    verify(await ui.outline())


async def test_a_degraded_entry_still_opens_with_its_output(ui):
    for i in range(LIVE_ENTRY_WINDOW + 1):
        ui.run(f"bash echo {i}", f"output {i}")
    await ui.click("bash echo 0")

    verify(await ui.outline())


async def test_a_running_tool_call_is_never_degraded(ui):
    ui.call("bash sleep 300")
    for i in range(LIVE_ENTRY_WINDOW + 3):
        ui.run(f"bash echo {i}")

    verify(await ui.outline())


async def test_a_diff_result_arriving_before_the_log_is_mounted_lands_in_its_call():
    diff = SingleToolResult(display_body="-old\n+new", display_language="diff")
    async with App().run_test() as pilot:
        tool_log = ToolLog()
        tool_log.add_tool_call("call-1", "replace-file-content a.txt")
        tool_log.add_tool_result("call-1", diff)
        await pilot.app.mount(tool_log)

        await eventually(
            pilot,
            lambda: tool_log.query_one("ToolCollapsible Contents Static.tool-result"),
            "the diff to be mounted inside the call's collapsible",
        )


def a_markdown_result(markdown: str) -> SingleToolResult:
    return SingleToolResult(display_body=markdown, display_language="markdown")


async def test_a_markdown_result_renders_as_markdown_widget(ui):
    ui.call("complete-task answer=done")
    ui.finish("complete-task answer=done", a_markdown_result("# Finished"))

    assert isinstance(await ui.body("complete-task answer=done"), Markdown)


async def test_a_degraded_markdown_entry_upgrades_to_markdown_widget(ui):
    ui.call("complete-task answer=done")
    ui.finish("complete-task answer=done", a_markdown_result("# Done"))
    for i in range(LIVE_ENTRY_WINDOW):
        ui.run(f"bash echo {i}")
    await ui.click("complete-task answer=done")

    assert isinstance(await ui.body("complete-task answer=done"), Markdown)


async def test_a_markdown_result_starts_flush_with_its_first_heading(ui):
    ui.call("subagent agenttype=coding")
    ui.finish(
        "subagent agenttype=coding",
        a_markdown_result("## Task\n\nsay hi\n\n## Result\n\ndone"),
    )

    rows, height = await ui.markdown_layout("subagent agenttype=coding")

    assert rows == [0, 2, 4, 6]
    assert height == 7
