#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mkdir -p "$repo/build"
exec 8>"$repo/build/build.lock"
flock 8
binary="$repo/build/lifeloop-search"
if [[ -x "$binary" && "$binary" -nt "$repo/native/search.cpp" && "$binary" -nt "$repo/native/safety.hpp" && "$binary" -nt "$repo/flake.nix" && "$binary" -nt "$repo/flake.lock" && "$binary" -nt "$repo/scripts/compile.sh" ]]; then
    exit 0
fi
temporary="$binary.tmp.$$"
trap 'rm -f "$temporary"' EXIT
"$repo/scripts/compiler_limiter.sh" g++ -std=c++20 -O3 -Wall -Wextra -Werror \
    "$repo/native/search.cpp" -o "$temporary"
mv "$temporary" "$binary"
