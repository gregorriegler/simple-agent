import logging
from simple_agent.infrastructure.textual.autocomplete import CompletionResult
from simple_agent.infrastructure.textual.widgets.file_loader import FileLoader
from simple_agent.infrastructure.textual.widgets.file_context_formatter import FileContextFormatter

logger = logging.getLogger(__name__)

class FileContextExpander:
    """
    Handles the expansion of file references in the user input.
    When the user submits text containing [📦path/to/file], this component
    reads the file and wraps it in <file_context> tags.
    """
    def __init__(self, file_loader: FileLoader = None, formatter: FileContextFormatter = None):
        self.file_loader = file_loader or FileLoader()
        self.formatter = formatter or FileContextFormatter()

    def expand(self, draft: CompletionResult) -> str:
        content = draft.text.strip()

        # Only process files that are actually referenced in the text
        # (This filters out files that were autocompleted but then deleted from text)
        active_references = draft.active_files

        if active_references:
            loaded_files = []
            for file_ref in active_references:
                file_path_str = file_ref.path
                file_text = self.file_loader.read_file(file_path_str)
                if file_text is not None:
                    loaded_files.append((file_path_str, file_text))

            file_contents = self.formatter.format(loaded_files)

            if file_contents:
                content += "\n" + file_contents

        return content
