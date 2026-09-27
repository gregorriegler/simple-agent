from __future__ import annotations

import re
from typing import Protocol

EMBEDDED_CONTENT = re.compile(r"\{\{([^{}]+\.md)\}\}")


class EmbeddedContent(Protocol):
    def read(self, name: str) -> str: ...


def embed_content(template: str, embedded_content: EmbeddedContent) -> str:
    return EMBEDDED_CONTENT.sub(
        lambda match: embedded_content.read(match.group(1)).rstrip("\n"), template
    )
