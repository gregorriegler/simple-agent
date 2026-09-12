"""Scripted tool calls for the stub LLMs, one builder per tool the tests call often."""

from simple_agent.application.tool_library import ToolCall


def cat(
    filename: str, line_range: str = "", with_line_numbers: bool = False
) -> ToolCall:
    arguments: dict = {"filename": filename}
    if line_range:
        arguments["line_range"] = line_range
    if with_line_numbers:
        arguments["with_line_numbers"] = True
    return ToolCall("cat", arguments)


def ls(path: str = "") -> ToolCall:
    return ToolCall("ls", {"path": path} if path else {})


def bash(command: str, background: bool = False) -> ToolCall:
    arguments: dict = {"command": command}
    if background:
        arguments["--background"] = True
    return ToolCall("bash", arguments)


def create_file(filename: str, content: str = "") -> ToolCall:
    return ToolCall("create-file", {"filename": filename, "content": content})


def replace_file_content(filename: str, content: str, mode: str = "single") -> ToolCall:
    return ToolCall(
        "replace-file-content",
        {"filename": filename, "replace_mode": mode, "content": content},
    )


def subagent(agenttype: str, task: str, background: bool = False) -> ToolCall:
    arguments: dict = {"agenttype": agenttype, "task_description": task}
    if background:
        arguments["--background"] = True
    return ToolCall("subagent", arguments)


def communicate_intent(intent: str) -> ToolCall:
    return ToolCall("communicate-intent", {"intent": intent})


def suggest(suggestion: str) -> ToolCall:
    return ToolCall("suggest", {"suggestion": suggestion})


def write_todos(content: str) -> ToolCall:
    return ToolCall("write-todos", {"content": content})


def complete_task(summary: str) -> ToolCall:
    return ToolCall("complete-task", {"summary": summary})
