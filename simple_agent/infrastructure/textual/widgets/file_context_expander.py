from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileContextExpander:
    def expand(self, content: str, referenced_files: set[str]) -> str:
        """
        Reads referenced files and appends their content wrapped in <file_context> tags.
        """
        if not referenced_files:
            return content

        file_contents = []
        for file_path_str in referenced_files:
            try:
                path = Path(file_path_str)
                if path.exists() and path.is_file():
                    file_text = path.read_text(encoding="utf-8")
                    file_contents.append(f'<file_context path="{file_path_str}">\n{file_text}\n</file_context>')
            except Exception as e:
                logger.error(f"Failed to read referenced file {file_path_str}: {e}")

        if file_contents:
            return content + "\n" + "\n".join(file_contents)
        return content
