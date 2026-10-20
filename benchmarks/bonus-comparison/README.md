# Starting bonus comparison — 2026-10-20

Compare the two current starting choices: **+100% job** and **+50% business**. All scores are cash after refunds at age 90. Each complete action path has been independently replayed. **These are best found routes, not proven global optima.**

Best found: **College, +50% business income, $9,155,745.00**. This route uses its one 140% refund at 90y00m on Globe Freight ($7,541,800 refunded).

The [prior +100% business research](../README.md), including Primary’s $27,896,953, remains unchanged. It uses a different permanent multiplier and is outside this two-option comparison.

| Education (start age) | +100% job | +50% business |
|---|---:|---:|
| None (10) | [$2,608,334.00](strategies/none-job.txt) | [$7,687,216.00](strategies/none-business-50.txt) |
| Primary (12) | [$3,441,355.00](strategies/primary-job.txt) | [$9,018,105.50](strategies/primary-business-50.txt) |
| Secondary (17) | [$3,260,417.00](strategies/secondary-job.txt) | [$8,231,691.00](strategies/secondary-business-50.txt) |
| College (19) | [$3,844,302.00](strategies/college-job.txt) | [$9,155,745.00](strategies/college-business-50.txt) |
| University (22) | [$3,925,391.00](strategies/university-job.txt) | [$8,913,187.00](strategies/university-business-50.txt) |

## Independent boost schedules

All ten routes use each of the three boosts exactly once. Income boosts start before that month’s payment and last 120 payments. Ages are years and months, so `15y07m` means 15 years, seven months.

| Education | Starting bonus | Job boost | Business boost | 140% refund | Refunded business |
|---|---|---|---|---|---|
| None | +100% job income | 10y01m | 80y00m | 90y00m | Skysoft |
| None | +50% business income | 10y05m | 79y09m | 89y11m | Globe Freight |
| Primary | +100% job income | 12y01m | 79y11m | 90y00m | Rapid Reach |
| Primary | +50% business income | 12y02m | 77y04m | 90y00m | Globe Freight |
| Secondary | +100% job income | 17y01m | 79y11m | 90y00m | Rapid Reach |
| Secondary | +50% business income | 17y01m | 78y11m | 90y00m | Globe Freight |
| College | +100% job income | 19y01m | 79y11m | 90y00m | Rapid Reach |
| College | +50% business income | 19y01m | 80y00m | 90y00m | Globe Freight |
| University | +100% job income | 22y02m | 79y11m | 90y00m | Rapid Reach |
| University | +50% business income | 22y01m | 78y11m | 90y00m | Globe Freight |

## Arithmetic and preserved results

Jay confirmed that Green Fork’s $35 base payment becomes exactly **$52.50** with the +50% starting bonus, or **$105** during its temporary business boost. Python replays preserve exact binary halves. Only the +50% scenario’s native protocol is scaled to integer half-dollar units; JSON cash values and all displayed results remain dollars. The job option reaches 4× base job income during its job boost; the +50% business option reaches 3× base business income during its business boost.

The existing reference JSON records, readable routes and 95-attempt matrix under `benchmarks/` are preserved byte-for-byte. New records live in [records/](records/), readable routes in [strategies/](strategies/), and comparison checkpoints in `runs/bonus-comparison/`. Committed comparison records are automatically loaded as floors on subsequent searches. Foreign scenarios contribute investment sequences only; cash, wages and action timing are recomputed under the target scenario.

## Search evidence and reproduction

The [comparison attempt matrix](attempts-2026-10-20.jsonl) contains **40 sequential attempts**. It retains each source revision/hash, beam width, ranking weight, native time/RSS and pruning, incumbent, refinement outcome and investment-template fingerprint. The source revision for this comparison is `efe109f5e42e7e0539c88ddcacf3b47d9791ab05`. Runs used native beams 64/96/128, ranking weights 100/200/50, and refinement budgets 30/20/30 seconds, followed by a beam-1 template refresh. Each native score is independently replayed before accepting a route. Full-game beam searches remain uncertified; local refinement fixed points do not establish global optimality.

The pinned Nix environment and native safety limits are unchanged: **768 MB aggregate memory, one CPU, zero swap, 64 tasks and a finite wall deadline**. Campaigns run sequentially. Native time excludes Python refinement; allow time for both.

Continue the ten current scenarios without overwriting the reference records:

```bash
MAX_SECONDS=550 ./scripts/run_safe.sh --compare-starting-bonuses --beam-width 64 --seconds 20 --polish-seconds 30
```

Replay the exact published scores and run the native/oracle, fractional-payment, checkpoint and containment regressions with `./scripts/run_tests_safe.sh`.
