from pathlib import Path
from simple_agent.infrastructure.project_tree import FileSystemProjectTree


def test_characterization_of_project_tree_rendering(tmp_path: Path):
    # Setup - "Legacy" state we want to preserve
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").touch()
    (tmp_path / "dir1" / "ignore_me.log").touch()
    (tmp_path / "file2.py").touch()
    (tmp_path / "folder_z").mkdir()
    (tmp_path / "file_a").touch()
    (tmp_path / ".gitignore").write_text("*.log\n")

    # Execution
    project_tree = FileSystemProjectTree(root_path=tmp_path)
    output = project_tree.render(max_depth=3)

    # Expectation - Locked down behavior
    # Note: treelib output format usually includes lines and the root node.
    # We will adjust this expectation after seeing the first failure or just infer it.
    # The root node in FileSystemProjectTree is hardcoded as "./" in create_node,
    # but the node_id is str(root_path).

    # Expectation - Locked down behavior
    # Using exact string match for the tree structure to ensure order and hierarchy are preserved.
    # Note: treelib output format depends on the order of insertion.

    # We expect directories first (default implementation behavior).
    # dir1/
    # ├── file1.txt
    # └── file2.py
    # ... but wait, file2.py is at root.

    # Let's inspect the actual output if we were using approval testing, but here we can just assert exact lines.
    # The expected sorted order is directories first, then files.
    # Root: ./
    # ├── dir1/
    # │   └── file1.txt
    # └── file2.py

    expected_output = """./
├── .gitignore
├── dir1/
│   └── file1.txt
├── file2.py
├── file_a
└── folder_z/
"""
    assert output.strip() == expected_output.strip()
