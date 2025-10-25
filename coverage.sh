#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ "${1-}" = "-h" ] || [ "${1-}" = "--help" ]; then
    printf "Usage: ./coverage.sh [target...]\n"
    printf "Without arguments prints files below 100%% coverage.\n"
    printf "With file or directory arguments shows detailed coverage and missing lines.\n"
    exit 0
fi

if ! uv run coverage run -m pytest tests/ -q > /dev/null 2>&1; then
    echo "❌ Tests failed"
    uv run pytest tests/ -q
    exit 1
fi

if [ "$#" -eq 0 ]; then
    echo "Coverage: Files < 100%"
    echo "----------------------"
    uv run coverage report --skip-empty --skip-covered | grep "^simple_agent" | awk '{printf "%-60s %6s %6s %7s\n", $1, $2, $3, $4}'
    echo ""
    uv run coverage report --skip-empty --skip-covered | grep "^TOTAL"
    echo ""
    uv run coverage report --skip-empty --skip-covered | grep "skipped"
    exit 0
fi

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
