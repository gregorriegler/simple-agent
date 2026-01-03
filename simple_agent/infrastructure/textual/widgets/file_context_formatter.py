from typing import List, Tuple

class FileContextFormatter:
    """
    Responsible for formatting loaded file contents into the XML format expected by the Agent.
    """
    def format(self, loaded_files: List[Tuple[str, str]]) -> str:
        file_contents = []
        for path_str, text in loaded_files:
            file_contents.append(f'<file_context path="{path_str}">\n{text}\n</file_context>')

        return "\n".join(file_contents)
