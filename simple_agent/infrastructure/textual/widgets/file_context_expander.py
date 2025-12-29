import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FileContextExpander:
    """
    Handles the expansion of file references in the user input.
    When the user submits text containing [📦path/to/file], this component
    reads the file and wraps it in <file_context> tags.
    """
    def expand(self, text: str, referenced_files: set[str]) -> str:
        content = text.strip()

        # Only process files that are actually referenced in the text
        # (This filters out files that were autocompleted but then deleted from text)
        active_references = {f for f in referenced_files if f"[📦{f}]" in content}

        if active_references:
            file_contents = []
            for file_path_str in active_references:
                try:
                    path = Path(file_path_str)
                    if path.exists() and path.is_file():
                        file_text = path.read_text(encoding="utf-8")
                        file_contents.append(f'<file_context path="{file_path_str}">\n{file_text}\n</file_context>')
                except Exception as e:
                    logger.error(f"Failed to read referenced file {file_path_str}: {e}")

            if file_contents:
                content += "\n" + "\n".join(file_contents)

        return content
