# Verified search results — 2026-10-20

All amounts are final cash after business refunds at age 90. These are best found routes, not proven global optima. Every published record passes independent Python replay. Full-game searches trim branches; finishing the horizon or a local refinement pass is not a global proof.

Primary education starts at age 12 and uses the FreshMart job track. The business catalog runs from Green Fork through Bright Core. Each of the three independent boosts may be used once: double job income for 120 payments, double business income for 120 payments, and one 140% business refund. All ten retained strategies use each boost exactly once.

| Education (start age) | +100% job bonus | +100% business bonus | Business gain this follow-up |
|---|---:|---:|---:|
| None (10) | $2,603,420 | $23,841,358 | +$515,172 |
| Primary (12) | $3,441,355 | $27,896,953 | +$1,262,052 |
| Secondary (17) | $3,260,067 | $24,495,230 | +$512,220 |
| College (19) | $3,844,302 | $26,837,672 | +$563,100 |
| University (22) | $3,925,391 | $25,253,906 | +$846,314 |

The leading Primary/business route increased from $26,634,901 to $27,896,953: +$1,262,052 (4.74%). Maximum education/business increased from $24,407,592 to $25,253,906: +$846,314. The original Python University/business baseline is $16,922,240, so the current gain over it is 49.2%.

## Independent boost schedules for the business starting bonus

| Education | Job boost starts | Business boost starts | 140% refund | Refunded business |
|---|---|---|---|---|
| None | 10y05m | 78y10m | 90y00m | Bright Core |
| Primary | 12y02m | 71y10m | 90y00m | Bright Core |
| Secondary | 17y01m | 77y02m | 90y00m | Bright Core |
| College | 19y01m | 72y08m | 90y00m | Bright Core |
| University | 22y01m | 74y05m | 90y00m | Bright Core |

The leading route refunds Bright Core for $19,306,000. Early immediate buy/refund and refund/rebuy funding remain legal search choices. These schedules show that job, business and refund boosts can occur at separate ages.

Complete readable paths for each education with the business starting bonus:

- [None](strategies/none-business.txt)
- [Primary](strategies/primary-business.txt)
- [Secondary](strategies/secondary-business.txt)
- [College](strategies/college-business.txt)
- [University](strategies/university-business.txt)

All ten machine-readable action paths are in [records/](records/).

## Education and job tracks

| Education | Starting age | Job track |
|---|---:|---|
| None | 10 | SunnySproutFields |
| Primary | 12 | FreshMart |
| Secondary | 17 | BrickLineWorks |
| College | 19 | ByteFixServices |
| University | 22 | DocuDynoCorp |

The historical attempt matrix preserves its original job-based education IDs:
`sunny-sprout`, `freshmart`, `brickline`, `bytefix`, `docudyno`, respectively.
Current checkpoint names and CLI choices use the education names above.
Relabelled checkpoints preserve their original action sequences, exact scores
and search statistics; all were independently replayed after relabelling.

## Search and reproduction

The [attempt matrix](campaign-2026-10-20.jsonl) contains 95 sequential bounded attempts, including 41 in this follow-up. It retains settings, source commit/hash, native time/RSS, candidates, pruning, completion state, refinement metrics and retained scores. The new campaign tested all five educations with both starting bonuses, tier changes paired with their eventual sales, investment omission, early refund/rebuy placement, monthly independent boost starts, and investment sequences transferred between starts. Transferred sequences are funded and retimed using the target scenario, without borrowing the source score. Newer attempts also fingerprint the templates they tried.

Follow-up campaigns used native beams 1/32/64, ranking weights 100/200, and refinement budgets 15/30/45 seconds. The earlier 54-attempt series also tried beams 128/256/512, ranking weights 75/125 and a no-diversity comparison. Later attempts retain previous verified floors; best_source=incumbent means that attempt retained rather than newly discovered its route. The final all-ten refresh reached a local fixed point in this restricted refinement space.

Latest runtime changes: `02a179395c112dec50be28ddaa90cf7042c37afa` (business choice and education templates), `88ddf4900fb7c6e7758dce65e121ce60a0b24040` (investment omission and template fingerprints). Each attempt pins its actual source revision. Earlier paths and scores remain available at prior benchmark commit `6e1dd747c2c595e02f9e27c51ab1b16addc3970e`. The matrix keeps attempt summaries; scenario files keep the strongest complete paths. Historical checkpoint paths identify the original worktree and are not runtime dependencies.

The pinned environment is unchanged: Python 3.13.15, GCC 15.3.0, systemd 260.4, original flake.lock. All jobs used 768 MB aggregate memory, one CPU, zero swap and a finite deadline; compiler processes remain serialized and capped. Native timing excludes Python refinement; total work is the sum of both phases. The original Python baseline took 1.132s and 16,596 KB RSS but expanded a smaller move set, so these are not controlled language-speed measurements.

Run another bounded ten-scenario refinement, retaining committed floors:

```bash
MAX_SECONDS=400 ./scripts/run_safe.sh --campaign --beam-width 64 --seconds 20 --polish-seconds 15 --income-weight 200
```

Replay the exact published scores with `./scripts/run_tests_safe.sh`. Search need not rediscover a route to validate its score. Checkpoints preserve routes and restart frontier exploration; they do not retain an exhaustive search graph.
