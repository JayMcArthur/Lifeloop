# Verified search results — 2026-10-20

All amounts are final cash after business refunds at age 90. These are best found routes, not proven global optima. Every published record passes independent Python replay. All full-game runs used lossy beam selection; a completed horizon is not a proof.

| Education | +100% job bonus | +100% business bonus |
|---|---:|---:|
| sunny-sprout | $2,406,093 | $23,326,186 |
| freshmart | $3,135,414 | $26,634,901 |
| brickline | $3,003,556 | $23,983,010 |
| bytefix | $3,583,553 | $26,274,572 |
| docudyno | $3,602,568 | $24,407,592 |

## Leading routes

| Scenario | Job boost starts | Business boost starts | Bright Core bought | 140% refund |
|---|---|---|---|---|
| freshmart/business | 12y02m | 79y00m | 88y08m | 90y00m |
| docudyno/business | 22y01m | 80y00m | 89y01m | 90y00m |

Both leading routes retain the refund for Bright Core: purchase price $13,790,000, 140% refund $19,306,000. The solver also explores immediate refund/rebuy funding during the round and final-month buy/refund payouts. Neither beat these retained routes in the recorded experiments.

Complete action paths: [FreshMart/business](strategies/freshmart-business.txt) and [DocuDyno/business](strategies/docudyno-business.txt). Machine-readable paths for all ten scenarios are in [records/](records/).

The original DocuDyno/business Python beam-64 baseline was $16,922,240 (1.132 seconds, 16,596 KB peak RSS). The current maximum-education route is $24,407,592, an increase of $7,485,352 (44.2%). The new search expands more legal actions and uses saved incumbents, so these timings are not a controlled language-speed comparison.

## Experiments and reproducibility

The locked environment reports Python 3.13.15, GCC 15.3.0 and systemd 260.4.
The existing Nix lockfile is unchanged.

The [attempt matrix](campaign-2026-10-20.jsonl) contains 54 sequential attempts, each with settings, source commit/hash, native time/RSS, candidates, pruning, completion state, polish results and the retained score. It includes all five educations and both bonuses, beams 64/128/256/512, ranking weights 75/100/125, and a no-diversity comparison on the leading scenario. Later attempts load earlier verified records as floors; `best_source: incumbent` means the retained route was not newly discovered in that attempt.

Runtime source was last committed at `972cdbe4e2b20541351ccd24778697b760b1bb9b`. Each attempt pins its own actual earlier source revision; the final records may retain routes discovered at earlier revisions. The matrix keeps each attempt, while scenario files keep the strongest route. Checkpoint paths in the matrix identify the original worktree and are historical, not required runtime paths.

Native peak RSS in the recorded campaign ranged from 4,088 to 4,768 KB. Each job was capped at 768 MB aggregate memory, one CPU, zero swap and a finite deadline; compiler jobs were serialized and separately capped. See the root README for safety entry points and setup.

Run a full-horizon narrow campaign, retaining these committed floors:

```bash
MAX_SECONDS=300 ./scripts/run_safe.sh --campaign --beam-width 64 --seconds 20 --polish-seconds 8
```

Reproduce scores exactly by replaying the committed records with `./scripts/run_tests_safe.sh`. Search is heuristic, with optional bounded retiming/refund refinement; replay does not require rediscovering a route. The result checkpoint is not a persisted exhaustive frontier.
