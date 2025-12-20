#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Clean up old coverage data
uv run coverage erase

badge_output=""
html_output=false

while [ "$#" -gt 0 ]; do
    case "$1" in
        --badge)
            badge_output="docs/coverage.svg"
            shift
            ;;
        --badge=*)
            badge_output="${1#--badge=}"
            shift
            ;;
        --html)
            html_output=true
            shift
            ;;
        -h|--help)
            printf "Usage: ./coverage.sh [--badge[=OUTPUT]] [--html] [target...]\n"
            printf "Without arguments, prints all files with less than 100%% coverage.\n"
            printf "Provide files or directories as targets to see detailed coverage and missing lines.\n"
            printf "Use --badge to generate a local coverage badge (default docs/coverage.svg).\n"
            printf "Use --html to generate an HTML report.\n"
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

if ! uv run coverage run --source simple_agent -m pytest tests/ -q -n 0 > /dev/null 2>&1; then
    echo "❌ Tests failed"
    uv run pytest tests/ -q
    exit 1
fi

if [ ${#@} -eq 0 ]; then
    echo "Coverage: Files < 100%"
    echo "-------------------------------------------------------------------------------------"
    printf "%-60s %6s %6s %7s\n" "Name" "Stmts" "Miss" "Cover"
    echo "-------------------------------------------------------------------------------------"
    uv run coverage report --skip-empty --skip-covered | grep "^simple_agent" | awk '{printf "%-60s %6s %6s %7s\n", $1, $2, $3, $4}'
    echo ""
    uv run coverage report --skip-empty --skip-covered | grep "^TOTAL"
    echo ""
    uv run coverage report --skip-empty --skip-covered | grep "skipped"
else
    for target in "$@"; do
        if [ -d "$target" ]; then
            include="$target/*"
        else
            include="$target"
        fi

        echo "Coverage: $target"
        echo "----------------------"
        if ! uv run coverage report -m --skip-empty --include="$include"; then
            echo "No coverage data"
            echo ""
            continue
        fi

        if [ -f "$target" ]; then
            coverage_json=$(mktemp)
            if uv run coverage json -o "$coverage_json" --include="$include" > /dev/null 2>&1; then
                uv run python - "$target" "$coverage_json" <<'PY'
import json
import os
import sys

target = sys.argv[1]
coverage_json_path = sys.argv[2]

with open(coverage_json_path, "r", encoding="utf-8") as handle:
    data = json.load(handle)

files = data.get("files", {})
target_norm = os.path.normcase(os.path.abspath(target))
match_key = None
for key in files:
    key_norm = os.path.normcase(os.path.abspath(key))
    if key_norm == target_norm:
        match_key = key
        break

if match_key is None:
    for key in files:
        if os.path.basename(key) == os.path.basename(target):
            match_key = key
            break

if match_key is None:
    print("")
    print("File view unavailable: coverage data for this file was not found.")
    sys.exit(0)

missing = set(files.get(match_key, {}).get("missing_lines", []))

print("")
print("File view (missing lines marked with !!)")
print("-------------------------------------------------------------------------------------")
with open(target, "r", encoding="utf-8") as handle:
    for line_number, line in enumerate(handle, start=1):
        marker = "!!" if line_number in missing else "  "
        print(f"{line_number:6d} {marker} {line.rstrip(chr(10))}")
PY
            else
                echo ""
                echo "File view unavailable: could not generate coverage json."
            fi
            rm -f "$coverage_json"
        fi

        echo ""
    done
fi

if [ -n "$badge_output" ]; then
    coverage_xml=$(mktemp)
    trap 'rm -f "$coverage_xml"' EXIT
    uv run coverage xml -o "$coverage_xml"
    mkdir -p "$(dirname "$badge_output")"
    uv run python coverage_badge.py --coverage-xml "$coverage_xml" --output "$badge_output"
    echo "Generated badge at $badge_output"
fi

if [ "$html_output" = true ]; then
    # Generate HTML report
    uv run coverage html
    echo "HTML report generated in htmlcov/index.html"
fi
