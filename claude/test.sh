#!/usr/bin/env bash
set -euo pipefail

test_path="${1:-.}"

if ! cd "$test_path" 2>/dev/null; then
    echo "Error: Directory '$test_path' not found" >&2
    exit 1
fi

if output=$(dotnet test 2>&1); then
    echo "✅ All tests passed"
else
    echo "❌ Tests failed:"
    echo "$output"
    exit 1
fi