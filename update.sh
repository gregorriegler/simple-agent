#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${1:-$SCRIPT_DIR}"
PROJECT_NAME="${2:-simple-agent}"

if [ ! -d "$REPO_DIR" ]; then
  echo "Repo directory not found: $REPO_DIR" >&2
  exit 1
fi

cd "$REPO_DIR"
git pull --ff-only
sudo docker compose -p "$PROJECT_NAME" up -d --build
