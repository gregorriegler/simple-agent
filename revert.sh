#!/usr/bin/env bash
set -euo pipefail

dir="${1:-.}"
cd "$dir"
git reset --hard HEAD
git clean -fd
