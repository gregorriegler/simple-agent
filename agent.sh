#!/usr/bin/env bash
set -euo pipefail

# Resolve the directory of this script, even if it's a symlink
PROJECT_ROOT=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)

if [ -f "$PROJECT_ROOT/.env" ]; then
    # Load environment variables, ignoring comments and empty lines
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | grep -v '^[[:space:]]*$' | xargs)
fi

exec uv run --project "$PROJECT_ROOT" --script "$PROJECT_ROOT/simple_agent/main.py" "$@"

