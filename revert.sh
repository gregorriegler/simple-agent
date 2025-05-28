#!/usr/bin/env bash
set -euo pipefail

# Set correct HOME path for Windows
export HOME="/mnt/c/Users/riegl"

dir="${1:-.}"
cd "$dir" || exit 1

git reset --hard HEAD
git clean -fd
