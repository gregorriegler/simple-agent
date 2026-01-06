from pathlib import Path

from treelib import Tree

from simple_agent.application.project_tree import ProjectTree


class FileSystemProjectTree(ProjectTree):
    def __init__(self, root_path: Path | None = None):
        self._root_path = root_path or Path(".")

    def render(self, max_depth: int = 2) -> str:
        root_path = self._root_path
        gitignore_patterns = _read_gitignore(root_path)
        tree = Tree()
        tree.create_node("./", str(root_path))
        _build_tree(
            root_path,
            tree,
            parent=str(root_path),
            max_depth=max_depth,
            gitignore_patterns=gitignore_patterns,
        )
        return tree.show(stdout=False)


def _read_gitignore(root_path: Path) -> set:
    gitignore_path = root_path / ".gitignore"
    patterns = set()

    if not gitignore_path.exists():
        return patterns

    with open(gitignore_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                pattern = line.rstrip("/")
                patterns.add(pattern)

    return patterns


def _should_ignore(path: Path, gitignore_patterns=None) -> bool:
    name = path.name

    if name == ".git":
        return True

    if name.startswith(".") and name != ".gitignore":
        return True

    if gitignore_patterns:
        for pattern in gitignore_patterns:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("*"):
                if name.startswith(pattern[:-1]):
                    return True
            elif pattern == name:
                return True
            elif "/" not in pattern and pattern in str(path):
                return True

    return False


def _build_tree(
    root_path: Path,
    tree: Tree,
    parent=None,
    max_depth=2,
    current_depth=0,
    gitignore_patterns=None,
):
    if current_depth >= max_depth:
        return

    try:
        items = root_path.iterdir()
    except PermissionError:
        return

    for item in items:
        if _should_ignore(item, gitignore_patterns):
            continue

        node_id = str(item)
        display_name = item.name + ("/" if item.is_dir() else "")

        tree.create_node(display_name, node_id, parent=parent)

        if item.is_dir():
            _build_tree(
                item,
                tree,
                parent=node_id,
                max_depth=max_depth,
                current_depth=current_depth + 1,
                gitignore_patterns=gitignore_patterns,
            )
