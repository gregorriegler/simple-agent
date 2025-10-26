from approvaltests import verify

from simple_agent.application.tool_library import ContinueResult
from simple_agent.infrastructure.console.console_display import ConsoleDisplay
from .print_spy import IOSpy


def test_console_display_with_different_indentations_and_agents():
    io_spy = IOSpy()

    agent = ConsoleDisplay(0, "Agent", io_spy)
    subagent = ConsoleDisplay(1, "Subagent", io_spy)
    subagent2 = ConsoleDisplay(2, "Subagent2", io_spy)

    agent.start_new_session()
    agent.assistant_says("Hello from Agent")
    agent.assistant_says("Multi-line message\nSecond line\nThird line")
    agent.tool_result(ContinueResult("Tool result"))
    agent.tool_result(ContinueResult("Multi-line tool result\nLine 2\nLine 3\nLine 4\nLine 5"))
    agent.exit()

    agent.continue_session()
    subagent.assistant_says("Hello from Subagent at indent 1")
    subagent.assistant_says("Another multi-line\nWith second line")
    subagent.tool_result(ContinueResult("Tool result at indent 1"))

    subagent2.assistant_says("Hello from Nested Subagent at indent 2")
    subagent2.assistant_says("Deep indentation\nWith multiple\nLines here")
    subagent2.tool_result(ContinueResult("Deep tool result\nWith lines"))
    subagent2.exit()

    verify(io_spy.get_output())
