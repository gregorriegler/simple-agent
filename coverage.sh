#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! output=$(uv run coverage run -m pytest tests/ 2>&1); then
    echo "$output"
    exit 1
fi

uv run coverage report