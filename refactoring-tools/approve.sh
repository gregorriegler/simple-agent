#!/bin/bash

# approve.sh - Approve test results by copying .received.txt to .verified.txt files
# Usage: ./approve.sh [test_name_pattern]
# Example: ./approve.sh RenameSymbol
# Example: ./approve.sh CanRenameUnusedLocalVariable

set -e

# Function to display usage
show_usage() {
    echo "Usage: $0 [test_name_pattern]"
    echo ""
    echo "Approve test results by copying .received.txt files to .verified.txt files"
    echo ""
    echo "Examples:"
    echo "  $0                           # Approve all received files"
    echo "  $0 RenameSymbol             # Approve all RenameSymbol test files"
    echo "  $0 CanRenameUnusedLocal     # Approve specific test"
    echo ""
    echo "The script will:"
    echo "  1. Find all .received.txt files matching the pattern"
    echo "  2. Copy each .received.txt to its corresponding .verified.txt"
    echo "  3. Delete the .received.txt file after successful copy"
}

# Check if help is requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Get the test name pattern (optional)
TEST_PATTERN="$1"

# Find the refactoring-tools directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REFACTORING_DIR="$SCRIPT_DIR"

# If we're not in refactoring-tools, try to find it
if [[ ! -d "$REFACTORING_DIR/RoslynRefactoring.Tests" && ! -d "$REFACTORING_DIR/RoslynAnalysis.Tests" ]]; then
    # Try parent directories
    PARENT_DIR="$(dirname "$SCRIPT_DIR")"
    if [[ -d "$PARENT_DIR/refactoring-tools" ]]; then
        REFACTORING_DIR="$PARENT_DIR/refactoring-tools"
    else
        echo "Error: Could not find refactoring-tools directory with test projects"
        echo "Please run this script from the refactoring-tools directory or its parent"
        exit 1
    fi
fi

echo "Working in directory: $REFACTORING_DIR"

# Build the find pattern
if [[ -n "$TEST_PATTERN" ]]; then
    FIND_PATTERN="*${TEST_PATTERN}*.received.txt"
    echo "Looking for received files matching pattern: $FIND_PATTERN"
else
    FIND_PATTERN="*.received.txt"
    echo "Looking for all received files: $FIND_PATTERN"
fi

# Find all .received.txt files matching the pattern
RECEIVED_FILES=$(find "$REFACTORING_DIR" -name "$FIND_PATTERN" -type f 2>/dev/null || true)

if [[ -z "$RECEIVED_FILES" ]]; then
    echo "No .received.txt files found matching pattern: $FIND_PATTERN"
    echo ""
    echo "This could mean:"
    echo "  - All tests are passing (no received files generated)"
    echo "  - The pattern doesn't match any files"
    echo "  - Tests haven't been run yet"
    echo ""
    echo "To generate .received.txt files, run failing tests first:"
    echo "  dotnet test"
    exit 0
fi

echo "Found received files:"
echo "$RECEIVED_FILES"
echo ""

# Process each received file
APPROVED_COUNT=0
FAILED_COUNT=0

while IFS= read -r received_file; do
    if [[ -z "$received_file" ]]; then
        continue
    fi
    
    # Generate the corresponding verified file name
    verified_file="${received_file%.received.txt}.verified.txt"
    
    echo "Approving: $(basename "$received_file")"
    echo "  From: $received_file"
    echo "  To:   $verified_file"
    
    # Copy received to verified
    if cp "$received_file" "$verified_file"; then
        echo "  ✓ Copied successfully"
        
        # Remove the received file
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
done <<< "$RECEIVED_FILES"

# Summary
echo "=== Summary ==="
echo "Approved: $APPROVED_COUNT files"
if [[ $FAILED_COUNT -gt 0 ]]; then
    echo "Failed: $FAILED_COUNT files"
    exit 1
else
    echo "All files processed successfully!"
fi