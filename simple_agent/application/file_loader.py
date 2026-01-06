from typing import Protocol


class FileLoader(Protocol):
    def read_file(self, file_path_str: str) -> str | None: ...
