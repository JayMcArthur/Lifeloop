# Ten-business strategies — 2026-10-21

All routes use **+100% permanent business income** and allow **10 businesses**. The ordinary round ends at **90**. The **optional five-year ad extension** ends at **95** and has separate strategies; select it before following an extended route. All three boosts remain independent and usable once each. Apply income boosts on the stated date for the next 120 payments.

| Education | Normal ending: 90 | With ad extension: 95 |
|---|---:|---:|
| None | [$23,880,358](age-90/strategies/none-business.txt) | [$30,416,998](age-95/strategies/none-business.txt) |
| Primary | [$27,901,533](age-90/strategies/primary-business.txt) | [$35,677,573](age-95/strategies/primary-business.txt) |
| Secondary | [$24,496,288](age-90/strategies/secondary-business.txt) | [$31,265,120](age-95/strategies/secondary-business.txt) |
| College | [$26,839,612](age-90/strategies/college-business.txt) | [$34,306,692](age-95/strategies/college-business.txt) |
| University | [$25,254,970](age-90/strategies/university-business.txt) | [$32,310,774](age-95/strategies/university-business.txt) |

Best found without the extension: **Primary, $27,901,533**. With the extension: **Primary, $35,677,573**. These bounded searches are **uncertified**, with no proof of global optimality. Every saved checkpoint independently replays to its published score.

## When to finish

- **Normal round:** sell every business by **89y11m**, then advance to **90y00m** for final salary and immediate game end.
- **With the ad extension:** continue through 90, sell every business by **94y11m**, then advance to **95y00m** for final salary and immediate game end. Do not follow the normal route’s liquidation date if using an extended route.

Each route lists when to apply the job/business boosts, their first and last boosted payments, every transaction and the one 140% refund. Actions consume no game time; new holdings earn on the next transition. The extension adds no extra uses of any boost.

## Primary routes

- **Ending at 90:** [full route](age-90/strategies/primary-business.txt), [replay checkpoint](age-90/records/primary-business.json). Apply job boost **12y01m**, business boost **71y09m**; final cash **$27,901,533**.
- **Ending at 95:** [full route](age-95/strategies/primary-business.txt), [replay checkpoint](age-95/records/primary-business.json). Apply job boost **12y01m**, business boost **84y10m**; final cash **$35,677,573**.

## Evidence and reproduction

The attempt logs for [90](age-90/attempts-2026-10-21.jsonl) and [95](age-95/attempts-2026-10-21.jsonl) retain each native result’s settings, actual code commit/hash, elapsed time/RSS, pruning/interruption status, independently replayed floor and refinement metrics. The 20 sequential attempts used beam 128 / rank 100 / 15s native / 15s refinement, then beam 32 / rank 200 / 20s native / 15s refinement for each of the ten scenarios. The first pass reached native time limits; the second completed all horizons with beam/depth trimming, so all remain uncertified. The runtime source is `f172873af5d00330fe6b6e29a927781c721ccd0e`. Original nine-slot records were validated under their original scenario before replaying their actions with the new capacity/horizon. Native and refinement scores always pass independent Python replay; old scores are never transferred.

All searches used the locked environment and safe runner: 768 MB aggregate job memory, one CPU, zero swap and finite deadlines. Runtime acceptance includes real containment and descendant timeout checks. A refinement fixed point does not establish global optimality.

```bash
MAX_SECONDS=90 ./scripts/run_safe.sh --education primary --bonus-years 0 --seconds 30 --polish-seconds 30
MAX_SECONDS=90 ./scripts/run_safe.sh --education primary --bonus-years 5 --seconds 30 --polish-seconds 30
```

Default output paths are separate (`runs/age-90/` and `runs/age-95/`), with actual limits in each checkpoint/signature/summary. Original nine-slot results remain in [the prior corrected dataset](../current/README.md); raw historical JSON and attempt logs remain unchanged. The original public +100% business route filenames now mirror the new ten-slot normal-ending routes.
