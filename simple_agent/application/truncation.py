MAX_TOOL_RESULT_CHARS = 30_000


def truncate(text: str, max_chars: int = MAX_TOOL_RESULT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    dropped = len(text) - max_chars
    head = max_chars // 2
    tail = max_chars - head
    return (
        f"{text[:head]}\n\n[... truncated {dropped} characters ...]\n\n{text[-tail:]}"
    )
