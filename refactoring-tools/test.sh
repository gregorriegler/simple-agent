#!/usr/bin/env bash
set -euo pipefail

test_path="${1:-.}"

if ! cd "$test_path" 2>/dev/null; then
    echo "Error: Directory '$test_path' not found" >&2
    exit 1
fi

# Create a temporary file for the test results
temp_file=$(mktemp)

# Run tests and capture output
if output=$(dotnet test --logger "console;verbosity=detailed" 2>&1 | tee "$temp_file"); then
    # Extract the number of passed tests
    passed_tests=$(grep -oP 'Passed: \K\d+' "$temp_file" || echo "0")
    echo "✅ All $passed_tests tests passed"
else
    echo "❌ Tests failed:"
    echo "$output"
    rm -f "$temp_file"
    exit 1
fi

# Clean up
rm -f "$temp_file"