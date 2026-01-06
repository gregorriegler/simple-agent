#!/usr/bin/env python
from __future__ import annotations

import argparse
import shlex

from textual_serve.server import Server


def build_command(app_args: list[str]) -> str:
    base = ["uv", "run", "--project", ".", "--script", "simple_agent/main.py"]
    if app_args:
        base.extend(app_args)
    return " ".join(shlex.quote(part) for part in base)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve the Simple Agent Textual app in a browser.",
    )
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--title", default=None)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "app_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to the Textual app (prefix with -- to separate).",
    )
    args = parser.parse_args()

    command = build_command(args.app_args)
    server = Server(command, host=args.host, port=args.port, title=args.title)
    server.serve(debug=args.debug)


if __name__ == "__main__":
    main()
