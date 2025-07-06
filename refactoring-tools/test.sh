#!/usr/bin/env bash
set -euo pipefail

test_path="${1:-.}"

if ! cd "$test_path" 2>/dev/null; then
    echo "Error: Directory '$test_path' not found" >&2
    exit 1
fi

# Run tests and capture output for RoslynRefactoring.Tests only
if output=$(dotnet test --logger "console;verbosity=detailed" 2>&1); then
    # Extract and sum all the "Total tests:" numbers
    passed_tests=$(echo "$output" | grep -oP 'Total tests: \K\d+' | awk '{sum += $1} END {print sum+0}')
    echo "✅ All $passed_tests tests passed"
else
    echo "❌ Tests failed:"
    echo "$output"
    exit 1
fi
