#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo"
exec nix --extra-experimental-features 'nix-command flakes' develop --no-update-lock-file --command \
    "$repo/scripts/run_limited.sh" "$repo/scripts/compile.sh"
