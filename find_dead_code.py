#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///

import ast
import os
import signal
import sys

TEST_REFERENCE_DIRS = ("tests",)


def iter_python_files(root_dir):
    python_files = []
    for base, _, files in os.walk(root_dir):
        for filename in files:
            if filename.endswith(".py"):
                python_files.append(os.path.join(base, filename))
    python_files.sort()
    return python_files


def collect_references(paths):
    references = set()
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                references.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                references.add(node.attr)
    return references


def is_factory_function(node, parent_class_name, class_names):
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            if not isinstance(child.value, ast.Call):
                continue
            func = child.value.func
            if isinstance(func, ast.Name):
                if parent_class_name and func.id in {parent_class_name, "cls"}:
                    return True
                if func.id in class_names:
                    return True
    return False


def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "simple_agent"

    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    if not os.path.isdir(root_dir):
        sys.stderr.write(f"Root directory not found: {root_dir}\n")
        sys.exit(1)

    python_files = iter_python_files(root_dir)
    test_reference_dirs = [
        dir_name for dir_name in TEST_REFERENCE_DIRS if os.path.isdir(dir_name)
    ]

    definitions = []
    production_references = collect_references(python_files)
    test_references = set()
    for reference_dir in test_reference_dirs:
        test_references.update(collect_references(iter_python_files(reference_dir)))

    for path in python_files:
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node

        class_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        }

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("__"):
                    parent_class = (
                        node.parent.name
                        if isinstance(node.parent, ast.ClassDef)
                        else None
                    )
                    is_factory = is_factory_function(node, parent_class, class_names)
                    definitions.append(
                        (path, "function", node.name, node.lineno, is_factory)
                    )
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("__"):
                    definitions.append((path, "class", node.name, node.lineno, False))
            elif isinstance(node, ast.Assign) and isinstance(node.parent, ast.Module):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("__"):
                        definitions.append(
                            (path, "variable", target.id, node.lineno, False)
                        )
            elif isinstance(node, ast.AnnAssign) and isinstance(
                node.parent, ast.Module
            ):
                target = node.target
                if isinstance(target, ast.Name) and not target.id.startswith("__"):
                    definitions.append(
                        (path, "variable", target.id, node.lineno, False)
                    )

    unused = []
    for path, kind, name, line, is_factory in definitions:
        if name not in production_references:
            if name in test_references and is_factory:
                continue
            if name in test_references:
                reason = "test_only"
            else:
                reason = "no_refs" if kind in {"function", "class"} else "no_reads"
            unused.append((path, kind, name, line, reason))

    unused.sort()
    if unused:
        print("PATH|KIND|NAME|LINE|REASON")
    for path, kind, name, line, reason in unused:
        print(f"{path}|{kind}|{name}|{line}|{reason}")


if __name__ == "__main__":
    main()
