"""Run replay-verified searches and resumable incumbent campaigns."""

import argparse
import json
import os
from pathlib import Path
import sys

from lifeloop.model import BUSINESSES, ActionKind, Education, Scenario, StartingBonus, age
from lifeloop.records import load_record, save_record
from lifeloop.solver import ROOT, solve


def print_route(scenario, result):
    print(f"Education: {scenario.education.value}; +100% {scenario.starting_bonus.value} income")
    for action in (*result.actions, *result.final_sales):
        detail = BUSINESSES[action.business].name if action.business is not None else "for 120 payments"
        if action.kind in (ActionKind.SELL, ActionKind.REFUND_BOOST):
            detail += f" → ${BUSINESSES[action.business].refund(action.kind == ActionKind.REFUND_BOOST):,}"
        print(f"{age(action.month)}: {action.kind.value} {detail}")
    print(f"Final cash after refunds: ${result.final_cash:,}")


def main():
    scope = Path("/proc/self/cgroup").read_text()
    if "lifeloop-limited-" not in scope:
        os.execv(str(ROOT / "scripts/run_safe.sh"), [str(ROOT / "scripts/run_safe.sh"), *sys.argv[1:]])
    parser = argparse.ArgumentParser(description="Safely bounded LifeLoop C++ search, verified by Python replay.")
    parser.add_argument("--education", choices=[e.value for e in Education], default="docudyno")
    parser.add_argument("--starting-bonus", choices=[b.value for b in StartingBonus], default="business")
    parser.add_argument("--beam-width", type=int, default=512)
    parser.add_argument("--seconds", type=int, default=10, help="native time budget per scenario")
    parser.add_argument("--memory-mb", type=int, default=768)
    parser.add_argument("--income-weight", type=int, default=100, help="ranking weight, 25..200 percent")
    parser.add_argument("--no-diversity", action="store_true")
    parser.add_argument("--campaign", action="store_true", help="search all five educations and both bonuses sequentially")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "runs")
    parser.add_argument("--incumbent", type=Path, help="a replay-valid checkpoint for a single scenario")
    parser.add_argument("--json", action="store_true", help="print one machine-readable summary per scenario")
    args = parser.parse_args()
    if args.campaign and args.incumbent:
        parser.error("--incumbent selects one scenario; campaign checkpoints load from --output-dir")
    scenarios = [Scenario(e, b) for e in Education for b in StartingBonus] if args.campaign else [
        Scenario(Education(args.education), StartingBonus(args.starting_bonus))]
    best = None
    try:
        for scenario in scenarios:
            path = args.output_dir / f"{scenario.education.value}-{scenario.starting_bonus.value}.json"
            seed = load_record(args.incumbent, scenario) if args.incumbent else None
            if path.exists():
                saved = load_record(path, scenario)
                if seed is None or saved.final_cash > seed.final_cash:
                    seed = saved
            baseline = ROOT / "benchmarks/records/python-baseline.json"
            if scenario == Scenario() and baseline.exists():
                saved = load_record(baseline, scenario)
                if seed is None or saved.final_cash > seed.final_cash:
                    seed = saved
            found = solve(scenario, args.beam_width, seconds=args.seconds, memory_mb=args.memory_mb,
                          diversity=not args.no_diversity, income_weight=args.income_weight, incumbent=seed)
            save_record(path, scenario, found.result, found.statistics)
            summary = {"education": scenario.education.value, "starting_bonus": scenario.starting_bonus.value,
                       "final_cash": found.result.final_cash, "checkpoint": str(path), **found.statistics}
            with (args.output_dir / "attempts.jsonl").open("a") as stream:
                stream.write(json.dumps(summary) + "\n")
            if args.json:
                print(json.dumps(summary), flush=True)
            else:
                print(f"{scenario.education.value}/{scenario.starting_bonus.value}: ${found.result.final_cash:,}; "
                      f"{found.statistics['status']}; {found.statistics['elapsed_seconds']:.2f}s; "
                      f"{found.statistics['peak_rss_kb'] / 1024:.1f} MB; "
                      f"certified={found.statistics['certified']}", flush=True)
            if best is None or found.result.final_cash > best[1].final_cash:
                best = (scenario, found.result)
        if not args.json:
            print_route(*best)
    except (ValueError, RuntimeError, OSError) as error:
        parser.exit(2, f"Search stopped: {error}\nExisting atomic checkpoints are unchanged.\n")


if __name__ == "__main__":
    main()
