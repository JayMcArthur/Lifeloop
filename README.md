# LifeLoop solver

A C++ search core explores investment and boost schedules. Python owns the
game data and independently replays every returned or loaded strategy.

## Build, test and search

Requires Nix flakes, x86_64 Linux, cgroup v2 and a running systemd user manager.
The repository's existing `flake.lock` pins Python 3.13.15, GCC and the native
toolchain. There are no Python or C++ package dependencies to install.

From the actual checkout or task worktree:

```bash
./scripts/build_safe.sh
./scripts/run_tests_safe.sh
./scripts/run_safe.sh
```

These commands restore the locked environment noninteractively. Builds are
serialized and cached locally in `build/`. Repeating setup leaves the lock
unchanged. A direct `python3 main.py` CLI launch enters the same safe runner.

The default is maximum education (DocuDyno), +100% business starting income,
beam 512 and ten seconds of native search. To search all ten combinations:

```bash
MAX_SECONDS=240 ./scripts/run_safe.sh --campaign --beam-width 512 --seconds 15
```

Select a scenario and a larger bounded run:

```bash
MAX_SECONDS=90 ./scripts/run_safe.sh --education docudyno --starting-bonus business --beam-width 2000 --seconds 60
```

Education choices: `sunny-sprout`, `freshmart`, `brickline`, `bytefix`, `docudyno`.
Starting bonus choices: `job`, `business`.

## Resource containment

All build, test and search jobs run in a verified systemd user scope. Defaults
are 768 MB total job memory, zero job swap, one CPU, 64 tasks and a finite wall
deadline. `MAX_MB` may select 256..1024 MB; larger overrides are rejected.
`MAX_SECONDS` controls the entire CLI/campaign deadline; `--seconds` is each
native search's earlier graceful-stop budget. Leave time for reporting/builds.

The compiler limiter additionally caps each compiler at 768 MB and serializes
compiler processes across LifeLoop worktrees. The native executable installs
hard address-space/CPU/core-dump limits and checks the real cgroup constraints
before allocating application state. It refuses an uncontained launch.
An earlier internal RSS budget leaves headroom before the hard memory ceiling.
Nested native processes stay in their supervisor's shared cgroup.

For another debug/native command, use the locked environment and bounded runner:

```bash
nix --extra-experimental-features 'nix-command flakes' develop --no-update-lock-file --command scripts/run_limited.sh COMMAND ARGS
```

## Results and continuation

Each scenario writes an atomic replay-verified checkpoint to
`runs/EDUCATION-BONUS.json`. Repeating the command loads it as a floor and injects
its valid prefixes into the next search. `runs/attempts.jsonl` records each run's
parameters, elapsed time, peak native RSS, candidate/pruning counts, completion
status, source commit/hash and whether the best route came from its incumbent.
Use `--output-dir DIR` to keep a separate campaign and `--json` for summary lines.
Use `--incumbent FILE` to seed a single scenario from an existing record.

An interrupted or failed run cannot overwrite an earlier checkpoint with a
partial file. Native time/memory stops return a valid completed strategy using
the best continuation found so far. A hard-killed process leaves the previous
checkpoint intact. Continuation preserves the best route; it restarts frontier
exploration and does not retain a persistent exhaustive search graph.

Recorded benchmark strategies live under `benchmarks/records/`. The original
Python beam-64 baseline is replay-verified at $16,922,240 for DocuDyno/business.
It is automatically retained as a floor for that scenario.

## Search behavior and limits

The native core uses compact portfolios, maximum-cash dominance for identical
future states, normalized expired boost clocks, and candidate accumulation
capped at twice the requested beam. It reserves part of the beam for distinct
used/unused boost combinations, inspired by Trading Caravan's continuation
lanes. `--no-diversity` enables controlled comparison; `--income-weight 25..200`
varies ranking emphasis on remaining business income (default 100).

Within a month, it explores repeated purchases and ordinary/boosted sales,
including selling and rebuying a business. Closure is bounded at 20 expansion
rounds. Ranking and beam trimming can lose promising routes, so **full-game
results are best found, not proven global optima**. `certified` is true only
when the configured scenario finishes with no lossy trimming and every monthly
trade closure reaches a fixed point. Tiny exhaustive-oracle tests verify this
path; interrupted, beam-trimmed or depth-limited runs are uncertified.

## Game rules

- The five education/job tracks start at ages 10, 12, 17, 19 and 22.
- Choose permanent +100% job or business income (2× base). Market is omitted.
- Own up to nine businesses, including multiple copies. All sixteen tiers run
  from Green Fork ($3,000, $35/month) to Bright Core ($13,790,000, $35,500/month).
- Activate each independent job/business boost once for 120 monthly payments.
  The boost multiplies its starting bonus for 4× base income in that category.
- Ordinary sales refund 70%; one business sale per round can refund 140%.
- DocuDyno upgrades to base $400 during age 71 years, six months. Its first
  $400 payment arrives at 71 years, seven months.

Boosts activate before the month's income; trades happen after income. New
businesses first earn next month. Payments begin one month after education
finishes and end before age 90. Remaining businesses sell at age 90; an unused
refund boost applies to one most expensive remaining business. Multiple copies
and final liquidation retain the prototype's assumptions. Repurchase of a sold
business is an explicit model assumption. Ages such as `71y06m` are years/months.

Project planning and decisions live in SilverBullet under `Projects/Lifeloop`.
