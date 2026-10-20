#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo"
LIMIT_MAX_MB=${MAX_MB:-768} LIMIT_MAX_SECONDS=${MAX_SECONDS:-180} \
    exec nix --extra-experimental-features 'nix-command flakes' develop --no-update-lock-file --command \
    "$repo/scripts/run_limited.sh" python3 "$repo/main.py" "$@"
