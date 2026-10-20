#!/usr/bin/env bash
set -euo pipefail

if (($# == 0)); then
    echo "[!] Usage: run_limited.sh <command> [args...]" >&2
    exit 2
fi

max_mb=${LIMIT_MAX_MB:-768}
max_seconds=${LIMIT_MAX_SECONDS:-180}

for value_name in max_mb max_seconds; do
    value=${!value_name}
    if [[ ! "$value" =~ ^[0-9]+$ ]]; then
        echo "[!] $value_name must be a non-negative integer" >&2
        exit 2
    fi
done
if ((max_mb < 256 || max_mb > 1024 || max_seconds == 0)); then
    echo "[!] Require 256<=LIMIT_MAX_MB<=1024 and LIMIT_MAX_SECONDS>0" >&2
    exit 2
fi
if ! command -v prlimit >/dev/null 2>&1; then
    echo "[!] prlimit is required; refusing an unbounded native run" >&2
    exit 2
fi
if ! command -v timeout >/dev/null 2>&1; then
    echo "[!] timeout is required; refusing an unbounded native run" >&2
    exit 2
fi
if ! command -v systemd-run >/dev/null 2>&1; then
    echo "[!] systemd-run with a user manager and cgroup v2 is required; refusing an uncontained job" >&2
    exit 2
fi

ulimit -c 0
scope_bytes=$((max_mb * 1024 * 1024))
as_bytes=$scope_bytes
inherited_as_kb=$(ulimit -Hv)
if [[ "$inherited_as_kb" =~ ^[0-9]+$ ]] && ((inherited_as_kb * 1024 < as_bytes)); then
    as_bytes=$((inherited_as_kb * 1024))
fi
command=(timeout --signal=TERM --kill-after=5s "${max_seconds}s"
         prlimit --as="$as_bytes" --core=0 -- "$@")

# Nested test/solver wrappers must stay in the outer job's cgroup. Starting
# another user scope would move them to a sibling and escape the aggregate cap.
scope_path=
while IFS=: read -r hierarchy controllers path; do
    if [[ "$hierarchy" == 0 && -z "$controllers" ]]; then
        scope_path=$path
    fi
done < /proc/self/cgroup
if [[ "${scope_path##*/}" == lifeloop-limited-*.scope ]]; then
    if [[ ! "${scope_path##*/}" =~ ^lifeloop-limited-([0-9]+)m-[0-9]+-[0-9]+\.scope$ ]]; then
        echo "[!] Unrecognized job scope; refusing native execution" >&2
        exit 2
    fi
    expected_job_bytes=$((BASH_REMATCH[1] * 1024 * 1024))
    cgroup="/sys/fs/cgroup$scope_path"
    read -r job_bytes < "$cgroup/memory.max"
    read -r swap_bytes < "$cgroup/memory.swap.max"
    read -r cpu_quota cpu_period < "$cgroup/cpu.max"
    read -r task_limit < "$cgroup/pids.max"
    read -r oom_group < "$cgroup/memory.oom.group"
    if [[ ! "$job_bytes" =~ ^[0-9]+$ || ! "$cpu_quota" =~ ^[0-9]+$ ||
          ! "$task_limit" =~ ^[0-9]+$ ]] ||
       ((job_bytes != expected_job_bytes || job_bytes > 1024 * 1024 * 1024 || swap_bytes != 0 ||
         cpu_quota > cpu_period || task_limit > 64 || oom_group != 1)); then
        echo "[!] Existing job scope lacks the required limits; refusing native execution" >&2
        exit 2
    fi
    echo "[*] Limited process: hard_cap=$((as_bytes / 1024 / 1024))MB timeout=${max_seconds}s existing_job_cap=$((job_bytes / 1024 / 1024))MB" >&2
    exec "${command[@]}"
fi

echo "[*] Limited job: memory=${max_mb}MB swap=0 cpu=1 tasks=64 timeout=${max_seconds}s" >&2
exec systemd-run --user --scope --quiet --collect --expand-environment=no \
    --unit="lifeloop-limited-${max_mb}m-$$-$RANDOM.scope" \
    --property="MemoryMax=$scope_bytes" \
    --property=MemorySwapMax=0 \
    --property=CPUQuota=100% \
    --property=TasksMax=64 \
    --property=OOMPolicy=kill \
    --property="RuntimeMaxSec=$((max_seconds + 5))s" \
    --property=TimeoutStopSec=5s \
    --property=KillMode=control-group \
    "${BASH_SOURCE[0]}" "$@"
