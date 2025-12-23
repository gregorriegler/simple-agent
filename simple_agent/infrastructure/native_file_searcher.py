import os
from pathlib import Path
from simple_agent.application.file_search import FileSearcher

class NativeFileSearcher(FileSearcher):
    def __init__(self, root_path: Path = Path(".")):
        self._root_path = root_path
        self._gitignore_patterns = self._read_gitignore(root_path)

    async def search(self, query: str) -> list[str]:
        # Simple implementation: walk and filter
        # In a real "fzf-like" scenario, we might want fuzzy matching.
        # For now, we'll do simple substring matching or prefix matching.
        
        results = []
        query = query.lower()
        
        # We can optimize this by caching the file list if needed, 
        # but for now we'll walk fresh to pick up new files.
        for root, dirs, files in os.walk(self._root_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if self._should_ignore(file_path):
                    continue
                
                # Get relative path for display/matching
                try:
                    rel_path = str(file_path.relative_to(self._root_path)).replace("\\", "/")
                except ValueError:
                    continue
                    
                if query in rel_path.lower():
                    results.append(rel_path)
                    if len(results) >= 50: # sensible limit for autocomplete
                        return results
        
        return sorted(results)

    def _read_gitignore(self, root_path: Path) -> set[str]:
        gitignore_path = root_path / ".gitignore"
        patterns = set()

        if not gitignore_path.exists():
            return patterns

        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Basic pattern normalization
                        pattern = line.rstrip("/")
                        patterns.add(pattern)
        except Exception:
            pass # Fail safe

        return patterns

    def _should_ignore(self, path: Path) -> bool:
        name = path.name

        if name == ".git":
            return True

        # Ignore hidden files/dirs (except .gitignore)
        if name.startswith(".") and name != ".gitignore":
            return True

        # Very basic gitignore matching (fnmatch style is better, but this mimics current project logic)
        if self._gitignore_patterns:
            for pattern in self._gitignore_patterns:
                # Handle simple glob cases that were in the original tree implementation
                if pattern.startswith("*"):
                    if name.endswith(pattern[1:]):
                        return True
                elif pattern.endswith("*"):
                    if name.startswith(pattern[:-1]):
                        return True
                elif pattern == name:
                    return True
                # Handle path segments
                elif "/" not in pattern and pattern in str(path):
                     # This is a bit aggressive (matches substrings anywhere), 
                     # but matches the previous logic.
                    return True
                
        return False
