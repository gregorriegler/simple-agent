#!/usr/bin/env bash
set -euo pipefail

dir="${1:-.}"
cd "$dir" || exit 1

git reset --hard HEAD
git clean -fd
