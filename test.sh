#!/usr/bin/env bash
set -euo pipefail

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
    echo "  -v, --verbose   Show verbose output with full tracebacks"
}

filter_pytest_output() {
    local output="$1"
    local verbose="$2"

    if [[ "$verbose" == true ]]; then
        # Verbose mode: only filter out deprecation warnings
        echo "$output" | grep -v "PytestDeprecationWarning" | grep -v "asyncio_default_fixture_loop_scope" | grep -v "warnings.warn" || echo "$output"
    else
        # Quiet mode: filter out deprecation warnings and pytest session header
        # Keep test progress, failures, and summary
        echo "$output" | \
            grep -v "PytestDeprecationWarning" | \
            grep -v "asyncio_default_fixture_loop_scope" | \
            grep -v "warnings.warn" | \
            grep -v "^platform " | \
            grep -v "^rootdir: " | \
            grep -v "^configfile: " | \
            grep -v "^plugins: " | \
            grep -v "^asyncio: mode=" | \
            grep -v "^collected " || true
    fi
}

verbose=false
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
    if [[ -f "tests/$1" ]]; then
        test_target="tests/$1"
    elif [[ -f "tests/${1}.py" ]]; then
        test_target="tests/${1}.py"
    else
        pytest_args+=(-k "$1")
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
