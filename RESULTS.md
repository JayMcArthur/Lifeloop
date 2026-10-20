# Saved LifeLoop strategies

Best found on 2026-10-20. Scores include all business refunds at age 90.
The +50% business starting bonus beats +100% job at every education tested.

## Best current choices

| Starting bonus | Best education | Final cash | Full route | Replay checkpoint |
|---|---|---:|---|---|
| **+50% business** | **College** | **$9,155,745** | [Every action](benchmarks/bonus-comparison/strategies/college-business-50.txt) | [JSON](benchmarks/bonus-comparison/records/college-business-50.json) |
| +100% job | University | $3,925,391 | [Every action](benchmarks/bonus-comparison/strategies/university-job.txt) | [JSON](benchmarks/bonus-comparison/records/university-job.json) |

Each route uses all three boosts once, at separate times:

| Milestone | College / +50% business | University / +100% job |
|---|---|---|
| Start | 19y00m | 22y00m |
| Job boost starts | 19y01m | 22y02m |
| First Green Fork | 21y10m | 23y01m |
| Business boost starts | 80y00m | 79y11m |
| Buy business for boosted refund | Globe Freight at 88y07m | Rapid Reach at 87y08m |
| 140% refund | Globe Freight at 90y00m: $7,541,800 | Rapid Reach at 90y00m: $2,945,600 |

Ages are years and months: `21y10m` means 21 years, ten months.
Use the full route for the purchases and sales between these milestones.

## All education starts

| Education (starting age) | +100% job | +50% business |
|---|---:|---:|
| None (10) | $2,608,334 | $7,687,216 |
| Primary (12) | $3,441,355 | $9,018,105.50 |
| Secondary (17) | $3,260,417 | $8,231,691 |
| College (19) | $3,844,302 | $9,155,745 |
| University (22) | $3,925,391 | $8,913,187 |

[All ten routes and boost schedules](benchmarks/bonus-comparison/README.md).
The [40-attempt comparison log](benchmarks/bonus-comparison/attempts-2026-10-20.jsonl)
records search settings, source revisions and refinement results.

## Preserved +100% business research

The earlier **Primary / +100% business** result is **$27,896,953**.
That uses a different permanent starting bonus from the current +50% comparison.
Its [full route](benchmarks/strategies/primary-business.txt),
[JSON checkpoint](benchmarks/records/primary-business.json),
[all reference results](benchmarks/README.md) and
[95-attempt log](benchmarks/campaign-2026-10-20.jsonl) remain unchanged.

## Rules and verification

Green Fork pays exactly $52.50 with +50% business, or $105 during the temporary
business boost. Job and business boosts each double their respective income for
120 payments; the one refund boost sells one business for 140%. The model allows
up to nine businesses, repeated copies, immediate trades, and final refunds.
Full rules and assumptions are in [README.md](README.md#game-rules).

Every saved checkpoint independently replays to its published score. These are
best found strategies; the full-game optimum is unproven. Run
`./scripts/run_tests_safe.sh` to verify the saved routes and solver checks.
Subsequent searches automatically retain the committed checkpoints as floors.
