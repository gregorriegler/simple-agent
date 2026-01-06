#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a coverage badge from coverage.xml"
    )
    parser.add_argument(
        "--coverage-xml",
        default="coverage.xml",
        dest="coverage_xml",
        help="Path to coverage.xml",
    )
    parser.add_argument(
        "--output",
        default="docs/coverage.svg",
        help="Output badge path",
    )
    return parser.parse_args()


def read_coverage_percent(xml_path: Path) -> float:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    line_rate = root.attrib.get("line-rate")
    if line_rate is None:
        raise ValueError("coverage.xml is missing the 'line-rate' attribute")
    return round(float(line_rate) * 100, 1)


def badge_color(percent: float) -> str:
    if percent >= 90:
        return "#4c1"  # brightgreen
    if percent >= 80:
        return "#97CA00"  # green
    if percent >= 70:
        return "#dfb317"  # yellow
    if percent >= 60:
        return "#fe7d37"  # orange
    return "#e05d44"  # red


def text_width(text: str) -> int:
    return 7 * len(text) + 10


def render_badge(percent: float) -> str:
    label = "coverage"
    value = f"{percent:.1f}%"

    label_width = text_width(label)
    value_width = text_width(value)
    total_width = label_width + value_width

    color = badge_color(percent)

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
    coverage_xml = Path(args.coverage_xml)
    if not coverage_xml.exists():
        raise FileNotFoundError(f"Coverage XML not found: {coverage_xml}")

    percent = read_coverage_percent(coverage_xml)
    badge_svg = render_badge(percent)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(badge_svg, encoding="utf-8")


if __name__ == "__main__":
    main()
