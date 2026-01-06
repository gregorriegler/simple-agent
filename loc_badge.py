#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a LoC badge from source files"
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        default=["simple_agent"],
        help="Files or directories to include when counting lines of code.",
    )
    parser.add_argument(
        "--output",
        default="docs/loc.svg",
        help="Output badge path",
    )
    return parser.parse_args()


def iter_python_files(paths: list[str]) -> list[Path]:
    repo_root = Path(__file__).parent
    files: list[Path] = []
    for entry in paths:
        path = repo_root / entry
        if path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
        elif path.suffix == ".py":
            files.append(path)
    return files


def count_loc(paths: list[str]) -> int:
    total = 0
    for file_path in iter_python_files(paths):
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    total += 1
    return total


def text_width(text: str) -> int:
    return 7 * len(text) + 10


def render_badge(lines_of_code: int) -> str:
    label = "loc"
    value = f"{lines_of_code:,}"

    label_width = text_width(label)
    value_width = text_width(value)
    total_width = label_width + value_width

    color = "#007ec6"  # blue

    return f"""
<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' width='{total_width}' height='20' role='img' aria-label='{label}: {value}'>
  <linearGradient id='s' x2='0' y2='100%'>
    <stop offset='0' stop-color='#bbb' stop-opacity='.1'/>
    <stop offset='1' stop-opacity='.1'/>
  </linearGradient>
  <clipPath id='r'>
    <rect width='{total_width}' height='20' rx='3' fill='#fff'/>
  </clipPath>
  <g clip-path='url(#r)'>
    <rect width='{label_width}' height='20' fill='#555'/>
    <rect x='{label_width}' width='{value_width}' height='20' fill='{color}'/>
    <rect width='{total_width}' height='20' fill='url(#s)'/>
  </g>
  <g fill='#fff' text-anchor='middle' font-family='DejaVu Sans,Verdana,Geneva,sans-serif' font-size='11'>
    <text x='{label_width / 2}' y='15'>{label}</text>
    <text x='{label_width + value_width / 2}' y='15'>{value}</text>
  </g>
</svg>
""".strip()


def main() -> None:
    args = parse_args()

    loc = count_loc(args.paths)
    badge_svg = render_badge(loc)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(badge_svg, encoding="utf-8")


if __name__ == "__main__":
    main()
