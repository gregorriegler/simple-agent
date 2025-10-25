#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! uv run coverage run -m pytest tests/ -q > /dev/null 2>&1; then
    echo "❌ Tests failed"
    uv run pytest tests/ -q
    exit 1
fi

echo "Coverage: Files < 100%"
echo "----------------------"
uv run coverage report --skip-empty --skip-covered | grep "^simple_agent" | awk '{printf "%-60s %6s %6s %7s\n", $1, $2, $3, $4}'
echo ""
uv run coverage report --skip-empty --skip-covered | grep "^TOTAL"
echo ""
uv run coverage report --skip-empty --skip-covered | grep "skipped"