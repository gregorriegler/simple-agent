from typing import Protocol, Optional


class FileLoader(Protocol):
    def read_file(self, file_path_str: str) -> Optional[str]: ...
