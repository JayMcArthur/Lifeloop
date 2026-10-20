# LifeLoop solver

A C++ search core explores investment and boost schedules. Python owns the
game data and independently replays every returned or loaded strategy.

The [recorded campaign](benchmarks/README.md) reaches **$26,634,901** with
FreshMart/+100% business income and **$24,407,592** with maximum education.
It includes complete action paths and all ten scenario records.

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
native search's earlier graceful-stop budget. `--polish-seconds` adds a bounded
Python refinement pass (default five seconds per scenario). Leave time for both
phases, reporting and builds.

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
its valid prefixes into the next search. An exclusive output-directory lock
rejects overlapping writers. `runs/attempts.jsonl` records each run's
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
The CLI automatically retains each scenario's committed best record as a floor,
as well as the original Python baseline for DocuDyno/business. Fresh checkouts
therefore keep the best recorded route even during a short search.

## Search behavior and limits

The native core uses compact portfolios, maximum-cash dominance for identical
future states, normalized expired boost clocks, and candidate accumulation
capped at twice the requested beam. It reserves part of the beam for distinct
used/unused boost combinations, inspired by Trading Caravan's continuation
lanes. Cash-rich continuations reserve room for multi-sale upgrades, and direct
sale/purchase pairs survive intermediate beam trimming. `--no-diversity` enables
controlled comparison; `--income-weight 25..200`
varies ranking emphasis on remaining business income (default 100).

Within a month, it explores repeated purchases and ordinary/boosted sales,
including immediate buy/refund pairs and selling and rebuying a business.
Its completion score also considers selling holdings normally after the last
payment, buying an affordable business and immediately refunding it at 140%.
Closure is bounded at 20 expansion
rounds. Ranking and beam trimming can lose promising routes, so **full-game
results are best found, not proven global optima**. `certified` is true only
when the configured scenario finishes with no lossy trimming and every monthly
trade closure reaches a fixed point. Tiny exhaustive-oracle tests verify this
path; interrupted, beam-trimmed or depth-limited runs are uncertified.

The refinement pass keeps a route's purchase/sale sequence, moves affordable
transaction blocks to their earliest month, scans monthly job/business boost
starts, and tries each recorded sale (or final liquidation) for the single
140% refund. It removes cash-losing ordinary sell/rebuy cycles. Only strict,
independently replayed improvements are accepted. It also tests an immediate
refund/rebuy after each recorded purchase to fund earlier subsequent upgrades.
A local fixed point in this
restricted refinement space is not a global certificate.

## Game rules

- The five education/job tracks start at ages 10, 12, 17, 19 and 22.
- Choose permanent +100% job or business income (2× base). Market is omitted.
- Own up to nine businesses, including multiple copies. All sixteen tiers run
  from Green Fork ($3,000, $35/month) to Bright Core ($13,790,000, $35,500/month).
- Activate each independent job/business boost once for 120 monthly payments.
  The boost multiplies its starting bonus for 4× base income in that category.
- Ordinary sales refund 70%; one business sale per round can refund 140%.
  Buying and refunding is immediate and consumes no game time, so the one-use
  refund may accelerate early investment or fund a final payout.
- DocuDyno upgrades to base $400 during age 71 years, six months. Its first
  $400 payment arrives at 71 years, seven months.

Boosts activate before the month's income; trades happen after income. New
businesses first earn next month. Payments begin one month after education
finishes and end before age 90. Remaining businesses sell at age 90; an unused
refund boost applies to one most expensive remaining business. Multiple copies
and final liquidation retain the prototype's assumptions. Repurchase of a sold
business is an explicit model assumption. Ages such as `71y06m` are years/months.

Project planning and decisions live in SilverBullet under `Projects/Lifeloop`.
