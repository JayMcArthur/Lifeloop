#!/usr/bin/env bash
set -euo pipefail

max_mb=${COMPILER_MAX_MB:-768}
if [[ ! "$max_mb" =~ ^[0-9]+$ ]] || ((max_mb < 256 || max_mb > 768)); then
    echo "[!] COMPILER_MAX_MB must be an integer from 256 through 768" >&2
    exit 2
fi
if ! command -v prlimit >/dev/null 2>&1 || ! command -v flock >/dev/null 2>&1; then
    echo "[!] prlimit and flock are required; refusing an unbounded compile" >&2
    exit 2
fi

# Serialize compiler processes across LifeLoop builds and worktrees.
exec 9>/tmp/lifeloop-solver-compiler.lock
flock 9
as_bytes=$((max_mb * 1024 * 1024))
exec prlimit --as="$as_bytes" --core=0 -- "$@"
