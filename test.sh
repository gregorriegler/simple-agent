#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! output=$(python -m pytest tests/ -v 2>&1); then
    echo "$output"
    exit 1
fi

passed_tests=$(echo "$output" | grep -c "PASSED" || echo "0")
echo "✅ All $passed_tests tests passed"
