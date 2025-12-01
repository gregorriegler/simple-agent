#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

badge_output=""

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
        -h|--help)
            printf "Usage: ./coverage.sh [--badge[=OUTPUT]] [target...]\n"
            printf "Without targets prints files below 100%% coverage.\n"
            printf "With targets shows detailed coverage and missing lines.\n"
            printf "Use --badge to generate a local coverage badge (default docs/coverage.svg).\n"
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

if ! uv run coverage run -m pytest tests/ -q > /dev/null 2>&1; then
    echo "❌ Tests failed"
    uv run pytest tests/ -q
    exit 1
fi

if [ ${#@} -eq 0 ]; then
    echo "Coverage: Files < 100%"
    echo "----------------------"
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
