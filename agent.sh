#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

exec uv run --script "$PROJECT_ROOT/simple_agent/main.py" "$@"
