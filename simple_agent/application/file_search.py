from typing import Protocol


class FileSearcher(Protocol):
    async def search(self, query: str) -> list[str]:
        """
        Search for files matching the query.

        Args:
            query: The search string (e.g., partial filename).

        Returns:
            A list of relative file paths matching the query.
        """
        ...
