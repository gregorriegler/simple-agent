from __future__ import annotations

import os

from simple_agent.application.embedded_content import EmbeddedContent


class FileSystemEmbeddedContent(EmbeddedContent):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def read(self, name: str) -> str:
        path = os.path.join(self.base_dir, name)
        with open(path, encoding="utf-8") as handle:
            return handle.read()
