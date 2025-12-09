#!/bin/bash

# approve.sh - Approve test results by copying .received.txt to .approved.txt files
# Usage: ./approve.sh [test_name_pattern]
# Example: ./approve.sh tool_library_test
# Example: ./approve.sh test_cat_tool

# Function to display usage
show_usage() {
    echo "Usage: $0 [test_name_pattern]"
    echo ""
    echo "Approve test results by copying .received.txt files to .approved.txt files"
    echo ""
    echo "Examples:"
    echo "  $0                           # Approve all received files"
    echo "  $0 tool_library_test         # Approve all tool_library_test files"
    echo "  $0 test_cat_tool             # Approve specific test"
    echo ""
    echo "The script will:"
    echo "  1. Find all .received.txt files matching the pattern"
    echo "  2. Copy each .received.txt to its corresponding .approved.txt"
    echo "  3. Delete the .received.txt file after successful copy"
}

# Check if help is requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Get the test name pattern (optional)
TEST_PATTERN="$1"

# Find the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
# Verify we can find the tests directory
if [[ ! -d "$PROJECT_DIR/tests" ]]; then
    echo "Error: Could not find tests directory"
    echo "Please run this script from the project root"
    exit 1
fi


# Build the find pattern
if [[ -n "$TEST_PATTERN" ]]; then
    FIND_PATTERN="*${TEST_PATTERN}*.received.txt"
    echo "Looking for received files matching pattern: $FIND_PATTERN"
else
    FIND_PATTERN="*.received.txt"
    echo "Looking for all received files: $FIND_PATTERN"
fi
echo "Working in directory: $PROJECT_DIR"

# Process each received file
APPROVED_COUNT=0
FAILED_COUNT=0

# Safely read from find without splitting
FOUND_ANY=0
while IFS= read -r received_file; do
    FOUND_ANY=1

    if [[ -z "$received_file" ]]; then
        continue
    fi

    approved_file="${received_file%.received.txt}.approved.txt"

    echo "Approving: $(basename "$received_file")"
    echo "  From: $received_file"
    echo "  To:   $approved_file"

    if cp "$received_file" "$approved_file"; then
        echo "  ✓ Copied successfully"
        if rm "$received_file"; then
            echo "  ✓ Removed received file"
            ((APPROVED_COUNT++))
        else
            echo "  ⚠ Warning: Could not remove received file"
            ((APPROVED_COUNT++))
        fi
    else
        echo "  ✗ Failed to copy file"
        ((FAILED_COUNT++))
    fi
    echo ""
done < <(find "$PROJECT_DIR" -type f -name "$FIND_PATTERN")
if [[ $FOUND_ANY -eq 0 ]]; then
    echo "No .received.txt files found matching pattern: $FIND_PATTERN"
    echo ""
    echo "This could mean:"
    echo "  - All tests are passing (no received files generated)"
    echo "  - The pattern doesn't match any files"
    echo "  - Tests haven't been run yet"
    echo ""
    echo "To generate .received.txt files, run failing tests first:"
    echo "  python -m pytest tests/ -v"
    exit 0
fi
# Summary
echo "=== Summary ==="
echo "Approved: $APPROVED_COUNT files"
if [[ $FAILED_COUNT -gt 0 ]]; then
    echo "Failed: $FAILED_COUNT files"
    exit 1
else
    echo "All files processed successfully!"
fi
