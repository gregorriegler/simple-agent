#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import shlex

from textual_serve.server import Server


def build_command(app_args: list[str]) -> str:
    base = ["uv", "run", "--project", ".", "--script", "simple_agent/main.py"]
    if app_args:
        base.extend(app_args)
    return " ".join(shlex.quote(part) for part in base)


def resolve_public_url(arg_value: str | None) -> str | None:
    if arg_value:
        return arg_value
    return os.environ.get("SIMPLE_AGENT_PUBLIC_URL")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve the Simple Agent Textual app in a browser.",
    )
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--title", default=None)
    parser.add_argument(
        "--public-url",
        default=None,
        help="Public URL used by the browser to reach the server.",
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "app_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to the Textual app (prefix with -- to separate).",
    )
    args = parser.parse_args()

    command = build_command(args.app_args)
    public_url = resolve_public_url(args.public_url)
    server = Server(
        command,
        host=args.host,
        port=args.port,
        title=args.title,
        public_url=public_url,
    )
    server.serve(debug=args.debug)


if __name__ == "__main__":
    main()
