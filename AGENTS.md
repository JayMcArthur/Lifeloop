# Native search safety

Build with `./scripts/build_safe.sh`, run tests with
`./scripts/run_tests_safe.sh`, and search with `./scripts/run_safe.sh`.
Use these bounded entry points for quick checks and benchmarks too.

For another native/debug command, use the locked environment and
`LIMIT_MAX_MB=768 LIMIT_MAX_SECONDS=180 ./scripts/run_limited.sh COMMAND ...`.
Keep native jobs at or below 1,024 MB, with one CPU, zero job swap, a finite
deadline, and serialized compilers. New native entry points install process
limits and verify cgroup containment before allocating application state.
Safety changes require the real kernel-limit and descendant-timeout tests.

Python owns game data and independent replay. Every search result and loaded
incumbent must pass replay. Label trimmed/interrupted searches as uncertified.
Read README.md for setup, result files and search assumptions.
