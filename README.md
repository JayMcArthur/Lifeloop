# LifeLoop solver

**[Saved results and winning strategies](RESULTS.md)** — start here for education
comparisons, exact boost timings and complete action paths.

A C++ search core explores investment and boost schedules. Python owns the
game data and independently replays every returned or loaded strategy.

The [current ten-slot business strategies](benchmarks/business-10/README.md) reach **$27,901,533 with Primary ending at 90**, or **$35,677,573 with Primary and the optional ad extension to 95**. These are bounded, independently replayed searches, without a proof of global optimality. [RESULTS.md](RESULTS.md) links every education’s full route for both endings.

The [prior nine-slot results](benchmarks/current/README.md) remain preserved, including the +50% business and +100% job comparisons; those two bonuses were not re-searched in this campaign.

The original public strategy filenames and reports now show the corrected
playable routes too. Raw historical JSON checkpoints and attempt logs remain
unchanged; earlier readable versions are preserved in Git history.

Business starts now default to **10 slots** (job starts retain nine). A normal round ends at **90**; use `--bonus-years 5` for the optional ad extension to **95**. The extension is a separate scenario with separate checkpoints. [RESULTS.md](RESULTS.md) links both new business-run guides.

Search Primary/+100% business with the extension:

```bash
MAX_SECONDS=90 ./scripts/run_safe.sh --education primary --bonus-years 5 --seconds 30 --polish-seconds 30
```

Continue the starting-bonus comparison:

```bash
MAX_SECONDS=550 ./scripts/run_safe.sh --compare-starting-bonuses --beam-width 64 --seconds 20 --polish-seconds 30
```

This searches all five educations, writes separate checkpoints under
`runs/age-90/bonus-comparison/`, and uses exact half-dollar business payments. Green Fork
pays $52.50 with the +50% starting bonus and $105 during its temporary 2× boost.

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

The default is University education (DocuDynoCorp job track), +100% business starting income,
beam 512 and ten seconds of native search. To search all fifteen combinations
(including +100% business):

```bash
MAX_SECONDS=400 ./scripts/run_safe.sh --campaign --beam-width 512 --seconds 15
```

Select a scenario and a larger bounded run (no extension unless requested):

```bash
MAX_SECONDS=90 ./scripts/run_safe.sh --education university --starting-bonus business --beam-width 2000 --seconds 60
```

Education choices: `none` (age 10), `primary` (12), `secondary` (17),
`college` (19), `university` (22). Their job tracks are SunnySproutFields,
FreshMart, BrickLineWorks, ByteFixServices and DocuDynoCorp, respectively.
Starting bonus choices: `job` (+100% job), `business-50` (+50% business),
and `business` (+100% business). The single-scenario default
remains University/+100% business; select `--starting-bonus business-50` for the 50% case.
`--campaign` explores all three cases; `--compare-starting-bonuses` selects the
two current alternatives above.

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
`runs/age-90/EDUCATION-BONUS.json` (or `runs/age-95/` with the extension). Repeating the command loads it as a floor and injects
its valid prefixes into the next search. An exclusive output-directory lock
rejects overlapping writers. the output directory’s `attempts.jsonl` records each run's
parameters, elapsed time, peak native RSS, candidate/pruning counts, completion
status, source commit/hash and whether the best route came from its incumbent.
Use `--output-dir DIR` to keep a separate campaign and `--json` for summary lines, including the slot limit and ending month. `--max-businesses N` explicitly selects 1..10 slots; its default output adds `slots-N/` to separate those checkpoints.
Use `--incumbent FILE` to seed a single scenario from an existing record.

An interrupted or failed run cannot overwrite an earlier checkpoint with a
partial file. Native time/memory stops return a valid completed strategy using
the best continuation found so far. A hard-killed process leaves the previous
checkpoint intact. Continuation preserves the best route; it restarts frontier
exploration and does not retain a persistent exhaustive search graph.

New ten-slot +100% business strategies live under `benchmarks/business-10/age-90/` and `age-95/`. Prior nine-slot strategies and the Python baseline remain under `benchmarks/current/records/`. The CLI validates each original checkpoint under its own scenario, then independently replays the same actions with any additional slots or years before using it as a floor. It never transfers an old score. Horizon and capacity participate in checkpoint signatures; mismatched checkpoints are rejected. Historical raw records and attempt logs remain preserved.

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
Its completion score also considers selling holdings normally on the last
actionable date, buying an affordable business and immediately refunding it at 140%.
Closure is bounded at 20 expansion rounds for up to nine slots and 22 for ten. Ranking and beam trimming can lose promising routes, so **full-game
results are best found, not proven global optima**. `certified` is true only
when the configured scenario finishes with no lossy trimming and every monthly
trade closure reaches a fixed point. Tiny exhaustive-oracle tests verify this
path; interrupted, beam-trimmed or depth-limited runs are uncertified.

The refinement pass moves affordable transaction blocks to their earliest month,
scans monthly job/business boost
starts, and tries each recorded sale (or final liquidation) for the single
140% refund. It removes cash-losing ordinary sell/rebuy cycles. Only strict,
independently replayed improvements are accepted. It also tests an immediate
refund/rebuy after each recorded purchase to fund earlier subsequent upgrades.
A local fixed point in this
restricted refinement space is not a global certificate.

It also varies or removes purchased business tiers together with their eventual sales and
tries saved investment sequences from the other education/bonus starts. Each
sequence is funded and retimed using the target scenario's own wages and boosts;
its original score and action ages do not transfer. The CLI reads templates from
committed records and its output directory. All three boosts are independent,
and each remains usable once per round.
Attempt statistics include the number and fingerprint of the templates tried.

## Game rules

- Education levels None, Primary, Secondary, College and University start at
  ages 10, 12, 17, 19 and 22, respectively.
- Starting bonuses supported here are +100% job (2× base), +100% business
  (2× base, the confirmed Primary playthrough), and +50% business (1.5× base).
  Market is omitted.
- Business starts allow ten businesses, including multiple copies. Job starts default to nine; use `--max-businesses` to select an explicit limit. All sixteen tiers run
  from Green Fork ($3,000, $35/month) to Bright Core ($13,790,000, $35,500/month).
- Activate each independent job/business boost once for 120 monthly payments.
  The boost multiplies its starting bonus: 4× job income with the job bonus,
  or 3× business income with the 50% business bonus (4× in the reference case).
- Ordinary sales refund 70%; one business sale per round can refund 140%.
  Buying and refunding is immediate and consumes no game time, so the one-use
  refund may accelerate early investment or fund a final payout.
- DocuDyno upgrades to base $400 during age 71 years, six months. Its first
  $400 payment arrives at 71 years, seven months.

Each monthly transition pays income, then actions occur on the displayed date.
Apply a boost on that date for the next 120 payments; the first boosted payment
arrives next month. New businesses also first earn next month. You can act at
the education starting date, before the first payment.

The normal ending is age **90**. The optional ad extension adds **five years**, for a maximum ending age of **95**. Sell all remaining businesses on **89y11m** normally, or **94y11m** with the extension; an unused refund boost applies to one most expensive remaining business. Advancing to the selected ending pays the final salary and immediately ends the game, with no further actions. Final salary cannot fund an
earlier purchase. The same last-action/final-payment ordering applies to custom
short horizons. Repurchase of a sold business remains an explicit model
assumption. Ages such as `71y06m` are years/months.

Project planning and decisions live in SilverBullet under `Projects/Lifeloop`.
