# Corrected monthly timing — 2026-10-21

These are existing saved routes replayed under the confirmed game timing, **without a new optimization search**. All action dates now say when to tap. The original raw records and 95-/40-attempt logs remain unchanged as historical evidence. The original public readable-route filenames now contain these corrected instructions too; previous readable versions are preserved in Git history.

## Actions on the displayed date

1. Each monthly transition credits income, then you can act on the displayed date.
2. Apply an income boost on that date; it affects the next 120 monthly payments. It does not boost the payment that just arrived. Each readable route lists the application date, first payment and last payment.
3. Buy a business on the displayed date; its first income arrives on the next transition. Purchases and sales do not advance time.
4. Sell everything by **89y11m**, including the one 140% refund. Moving to **90y00m** credits the final salary and immediately ends the game; no purchases, sales or boost activations are possible then. That final salary cannot fund an 89y11m trade.

## Primary / +100% business

[Complete playable route](strategies/primary-business.txt), [replay checkpoint](records/primary-business.json).

- Apply the job boost at **12y01m**. Its first boosted payment is12y02m and its last is22y01m.
- Buy the first Green Fork at **19y00m**, with **$3,006** available.
- Applying at 12y02m instead leaves **$2,988 at 19y00m** and **$3,058 at 19y01m**, matching the observed delay.
- Apply the business boost at **71y09m**, for payments71y10m through 81y09m.
- At **89y11m**, refund Bright Core for 140% ($19,306,000) and sell all remaining businesses for 70%.
- Advance to90 for the final $140 salary. Corrected final cash is **$27,897,093**.

## All saved scenarios

| Education (start age) | +100% job | +100% business | +50% business |
|---|---:|---:|---:|
| None (10) | [$2,608,494.00](strategies/none-job.txt) | [$23,841,438.00](strategies/none-business.txt) | [$7,687,296.00](strategies/none-business-50.txt) |
| Primary (12) | [$3,441,635.00](strategies/primary-job.txt) | [$27,897,093.00](strategies/primary-business.txt) | [$9,018,245.50](strategies/primary-business-50.txt) |
| Secondary (17) | [$3,260,757.00](strategies/secondary-job.txt) | [$24,495,400.00](strategies/secondary-business.txt) | [$8,231,861.00](strategies/secondary-business-50.txt) |
| College (19) | [$3,844,942.00](strategies/college-job.txt) | [$26,837,992.00](strategies/college-business.txt) | [$9,156,065.00](strategies/college-business-50.txt) |
| University (22) | [$3,926,191.00](strategies/university-job.txt) | [$25,254,306.00](strategies/university-business.txt) | [$8,913,587.00](strategies/university-business-50.txt) |

The current directory holds 15 scenario checkpoints plus the corrected original Python baseline. Each has a readable route in [strategies/](strategies/) and an independently replayed JSON record in [records/](records/).

## Preservation and provenance

Raw historical JSON records and attempt matrices under `../records/` and `../bonus-comparison/records/` remain unchanged. The public readable strategy paths under `../strategies/` and `../bonus-comparison/strategies/` now match the corrected current routes, so earlier live links are safe to follow. Original readable versions and reports are recoverable in [Git history](https://github.com/JayMcArthur/Lifeloop/tree/be1a69a748faaa58a081a05f740be218d4d8df83/benchmarks). Corrections use the same purchase/sale sequences, move each income boost one month before its old first-payment label, liquidate on the last actionable date and include final salary. Where two historical job routes existed, the stronger corrected route was retained.

Each corrected record pins the original record path, SHA256 and source commit `be1a69a748faaa58a081a05f740be218d4d8df83`, its historical score and the correction applied. Records are marked `fresh_search: false` and uncertified. Their rule signatures differ from the old phase convention: old checkpoints are rejected rather than treated as current scores. Fresh output defaults to `runs/current/` (or `runs/current/bonus-comparison/` for the two-option comparison).

The boost-date correction preserves the old effective income window. For these saved routes, the numerical score change is the newly included final salary. These remain best found routes; global optimality is unproven.

Run `./scripts/run_tests_safe.sh` to check replay, monthly timing, native/oracle parity and containment. Managed workspaces run substantial checks through `workspace heavy run --label PURPOSE -- COMMAND...`, while retaining the repository's bounded entry points.
