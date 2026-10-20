#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"$repo/scripts/build_safe.sh"
cd "$repo"
exec nix --extra-experimental-features 'nix-command flakes' develop --no-update-lock-file --command \
    "$repo/scripts/run_limited.sh" python3 -m unittest discover -s tests -v
