#!/usr/bin/env bash
set -euo pipefail

# 1) formatting
if ! output=$(uv run ruff format -v . 2>&1); then
    echo "$output"
    exit 1
fi
if [[ "$output" == *"reformatted"* ]]; then
    echo "$output" | grep "reformatted"
fi

# 2) lint (no auto-fix in CI/test script)
if ! output=$(uv run ruff check . 2>&1); then
    echo "$output"
    exit 1
fi

show_help() {
    echo "Usage: ./test.sh [OPTIONS] [TEST_PATTERN]"
    echo ""
    echo "Run pytest tests for the project."
    echo ""
    echo "Arguments:"
    echo "  TEST_PATTERN    Optional pattern to match specific tests"
    echo "                  Examples:"
    echo "                    ./test.sh test_foo.py        Run tests in test_foo.py"
    echo "                    ./test.sh test_foo           Run tests matching 'test_foo'"
    echo "                    ./test.sh 'test_foo and bar' Run tests matching expression"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message and exit"
    echo "  -v, --verbose   Show verbose output with progress and full tracebacks"
}

filter_pytest_output() {
    local output="$1"
    local verbose="$2"
    
    if [[ "$verbose" == true ]]; then
        # Verbose mode: show everything
        echo "$output"
    else
        # Quiet mode: only hide pytest session header boilerplate, keep everything else
        local in_failure_section=false
        
        while IFS= read -r line; do
            # Detect if we're in the FAILURES/ERRORS section
            if [[ "$line" == *"FAILURES"* ]] || [[ "$line" == *"ERRORS"* ]]; then
                in_failure_section=true
            fi
            
            # Check if we're at the short test summary
            if [[ "$line" == *"short test summary"* ]]; then
                in_failure_section=true
            fi
            
            # Show lines that are:
            # 1. In the FAILURES/ERRORS section (or test summary)
            # 2. Empty lines between sections
            # Keep all warnings and errors - only filter pytest session header info
            if [[ "$in_failure_section" == true ]] || [[ -z "$line" ]]; then
                # Only skip pytest session header lines
                if [[ "$line" != *"test session starts"* ]] && \
                   [[ "$line" != "platform"* ]] && \
                   [[ "$line" != "rootdir:"* ]] && \
                   [[ "$line" != "configfile:"* ]] && \
                   [[ "$line" != "plugins:"* ]] && \
                   [[ "$line" != "asyncio:"* ]] && \
                   [[ "$line" != "collected"* ]]; then
                    echo "$line"
                fi
            fi
        done <<< "$output"
    fi
}

verbose=false
file_provided=false
patterns=()
while [[ "${1:-}" == -* ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

export USE_APPROVE_SH_REPORTER=true

cd "$(dirname "$0")"

test_target="tests/"
if [[ "$verbose" == true ]]; then
    pytest_args=(-v)
else
    pytest_args=(-x --tb=short)
fi

if [[ -n "${1:-}" ]]; then
    # Collect all remaining arguments as patterns
    while [[ -n "${1:-}" ]]; do
        if [[ -f "$1" ]]; then
            # Full path provided
            test_target="$1"
            file_provided=true
        elif [[ -f "tests/$1" ]]; then
            test_target="tests/$1"
            file_provided=true
        elif [[ -f "tests/${1}.py" ]]; then
            test_target="tests/${1}.py"
            file_provided=true
        else
            # Treat as a pattern for -k flag
            patterns+=("$1")
        fi
        shift
    done
    
    # If we have patterns (and no file was provided), combine them with 'or'
    # If a file was provided, ignore remaining patterns
    if [[ ${#patterns[@]} -gt 0 ]] && [[ "$file_provided" == false ]]; then
        pattern_expr=$(printf ' or %s' "${patterns[@]}" | sed 's/^ or //')
        pytest_args+=(-k "$pattern_expr")
    fi
fi

if ! output=$(uv run pytest "$test_target" "${pytest_args[@]}" 2>&1); then
    filtered_output=$(filter_pytest_output "$output" "$verbose")
    echo "$filtered_output"
    exit 1
fi

filtered_output=$(filter_pytest_output "$output" "$verbose")
echo "$filtered_output"

passed_tests=$(echo "$output" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
echo "✅ All $passed_tests tests passed"
