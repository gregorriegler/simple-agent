#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///

import ast
import os
import signal
import sys

def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "simple_agent"
    
    if hasattr(signal, 'SIGPIPE'):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    
    if not os.path.isdir(root_dir):
        sys.stderr.write(f"Root directory not found: {root_dir}\n")
        sys.exit(1)
    
    python_files = []
    for base, _, files in os.walk(root_dir):
        for filename in files:
            if filename.endswith(".py"):
                python_files.append(os.path.join(base, filename))
    
    python_files.sort()
    
    definitions = []
    references = set()
    
    for path in python_files:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError:
            continue
        
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("__"):
                    definitions.append((path, "function", node.name, node.lineno))
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("__"):
                    definitions.append((path, "class", node.name, node.lineno))
            elif isinstance(node, ast.Assign) and isinstance(node.parent, ast.Module):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("__"):
                        definitions.append((path, "variable", target.id, node.lineno))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.parent, ast.Module):
                target = node.target
                if isinstance(target, ast.Name) and not target.id.startswith("__"):
                    definitions.append((path, "variable", target.id, node.lineno))
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                references.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                references.add(node.attr)
    
    unused = []
    for path, kind, name, line in definitions:
        if name not in references:
            reason = "no_refs" if kind in {"function", "class"} else "no_reads"
            unused.append((path, kind, name, line, reason))
    
    unused.sort()
    if unused:
        print("PATH|KIND|NAME|LINE|REASON")
    for path, kind, name, line, reason in unused:
        print(f"{path}|{kind}|{name}|{line}|{reason}")

if __name__ == "__main__":
    main()