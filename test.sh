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
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

export USE_APPROVE_SH_REPORTER=true

cd "$(dirname "$0")"

test_target="tests/"
pytest_args=(-v)

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
    echo "$output"
    exit 1
fi

passed_tests=$(echo "$output" | grep -c "PASSED" || echo "0")
echo "✅ All $passed_tests tests passed"
