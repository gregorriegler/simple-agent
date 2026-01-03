import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DiskFileLoader:
    def read_file(self, file_path_str: str) -> Optional[str]:
        try:
            path = Path(file_path_str)
            if path.exists() and path.is_file():
                return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read referenced file {file_path_str}: {e}")
        return None
