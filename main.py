"""Run replay-verified searches and resumable incumbent campaigns."""

import argparse
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import sys

from lifeloop.model import (BONUS_MONTHS, BOOST_MONTHS, BUSINESSES, END_MONTH, MAX_BUSINESSES,
                           INCOME_BOOSTS, ActionKind, Education, Scenario, StartingBonus, age, replay)
from lifeloop.records import campaign_lock, load_record, save_record
from lifeloop.polish import polish
from lifeloop.solver import ROOT, SearchResult, solve


def print_route(scenario, result):
    print(f"Education: {scenario.education.label}; job track: {scenario.education.job_track}; "
          f"{scenario.starting_bonus.label}")
    extension = "; includes the optional five-year ad extension" if scenario.end_month > END_MONTH else ""
    print(f"Business slots: {scenario.max_businesses}; ending age: {age(scenario.end_month)}{extension}")
    for action in (*result.actions, *result.final_sales):
        if action.kind in INCOME_BOOSTS:
            print(f"{age(action.month)}: apply {action.kind.value} "
                  f"(first payment {age(action.month + 1)}; "
                  f"last payment {age(min(action.month + BOOST_MONTHS, scenario.end_month))})")
            continue
        detail = BUSINESSES[action.business].name if action.business is not None else "for 120 payments"
        if action.kind in (ActionKind.SELL, ActionKind.REFUND_BOOST):
            detail += f" → ${BUSINESSES[action.business].refund(action.kind == ActionKind.REFUND_BOOST):,}"
        print(f"{age(action.month)}: {action.kind.value} {detail}")
    print(f"{age(scenario.end_month)}: final salary payment; game ends immediately (no actions)")
    print(f"Final cash after refunds: ${result.final_cash:,.2f}")


def main():
    scope = Path("/proc/self/cgroup").read_text()
    if "lifeloop-limited-" not in scope:
        os.execv(str(ROOT / "scripts/run_safe.sh"), [str(ROOT / "scripts/run_safe.sh"), *sys.argv[1:]])
    parser = argparse.ArgumentParser(description="Safely bounded LifeLoop C++ search, verified by Python replay.")
    parser.add_argument("--education", choices=[e.value for e in Education], default="university")
    parser.add_argument("--starting-bonus", choices=[b.value for b in StartingBonus], default="business")
    parser.add_argument("--bonus-years", type=int, choices=(0, 5), default=0,
                        help="optional ad extension: 0 ends at 90 (default), 5 ends at 95")
    parser.add_argument("--max-businesses", type=int, choices=range(1, MAX_BUSINESSES + 1),
                        help="business slots (default: 10 for business starts, 9 for job)")
    parser.add_argument("--beam-width", type=int, default=512)
    parser.add_argument("--seconds", type=int, default=10, help="native time budget per scenario")
    parser.add_argument("--memory-mb", type=int, default=768)
    parser.add_argument("--income-weight", type=int, default=100, help="ranking weight, 25..200 percent")
    parser.add_argument("--polish-seconds", type=float, default=5, help="bounded boost/refund retiming after native search")
    parser.add_argument("--no-diversity", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--campaign", action="store_true", help="search all educations and all three recorded bonus cases")
    modes.add_argument("--compare-starting-bonuses", action="store_true",
                       help="compare +100% job against +50% business for all five educations")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--incumbent", type=Path, help="a replay-valid checkpoint for a single scenario")
    parser.add_argument("--json", action="store_true", help="print one machine-readable summary per scenario")
    args = parser.parse_args()
    if args.output_dir is None:
        args.output_dir = ROOT / "runs" / f"age-{90 + args.bonus_years}"
        if args.max_businesses is not None:
            args.output_dir /= f"slots-{args.max_businesses}"
        if args.compare_starting_bonuses:
            args.output_dir /= "bonus-comparison"
    if not math.isfinite(args.polish_seconds) or not 0 <= args.polish_seconds <= 60:
        parser.error("--polish-seconds must be finite and between zero and 60")
    if (args.campaign or args.compare_starting_bonuses) and args.incumbent:
        parser.error("--incumbent selects one scenario; campaign checkpoints load from --output-dir")
    if args.compare_starting_bonuses:
        bonuses = (StartingBonus.JOB, StartingBonus.BUSINESS_50)
    else:
        bonuses = tuple(StartingBonus)
    def selected_scenario(education, bonus):
        slots = args.max_businesses if args.max_businesses is not None else (9 if bonus == StartingBonus.JOB else 10)
        return Scenario(education, bonus, max_businesses=slots,
                        end_month=END_MONTH + (BONUS_MONTHS if args.bonus_years else 0))

    scenarios = [selected_scenario(e, b) for e in Education for b in bonuses] if (
        args.campaign or args.compare_starting_bonuses) else [
            selected_scenario(Education(args.education), StartingBonus(args.starting_bonus))]
    best = None
    recorded_directories = ((ROOT / "benchmarks/current/records", 9, END_MONTH),
                            (ROOT / "benchmarks/business-10/age-90/records", 10, END_MONTH),
                            (ROOT / "benchmarks/business-10/age-95/records", 10, END_MONTH + BONUS_MONTHS))
    try:
        with campaign_lock(args.output_dir):
            for scenario in scenarios:
                path = args.output_dir / f"{scenario.education.value}-{scenario.starting_bonus.value}.json"
                seed = load_record(args.incumbent, scenario) if args.incumbent else None
                if path.exists():
                    saved = load_record(path, scenario)
                    if seed is None or saved.final_cash > seed.final_cash:
                        seed = saved
                for directory, slots, end in recorded_directories:
                    if slots > scenario.max_businesses or end > scenario.end_month:
                        continue
                    source = replace(scenario, max_businesses=slots, end_month=end)
                    floors = [directory / path.name]
                    if scenario.education == Education.UNIVERSITY and scenario.starting_bonus == StartingBonus.BUSINESS:
                        floors.append(directory / "python-baseline.json")
                    for floor in floors:
                        if floor.exists():
                            # Validate its original score before replaying the same
                            # actions with extra slots or a longer horizon.
                            saved = replay(scenario, load_record(floor, source).actions)
                            if seed is None or saved.final_cash > seed.final_cash:
                                seed = saved
                found = solve(scenario, args.beam_width, seconds=args.seconds, memory_mb=args.memory_mb,
                              diversity=not args.no_diversity, income_weight=args.income_weight, incumbent=seed)
                templates = {}
                if args.polish_seconds:
                    for education in Education:
                        for bonus in StartingBonus:
                            sources = (*recorded_directories,
                                       (args.output_dir, selected_scenario(education, bonus).max_businesses,
                                        scenario.end_month))
                            for directory, slots, end in sources:
                                source = Scenario(education, bonus, max_businesses=slots, end_month=end)
                                template = directory / f"{education.value}-{bonus.value}.json"
                                if template.exists():
                                    route = load_record(template, source)
                                    templates[route.actions] = None
                refined, metrics = polish(scenario, found.result, args.polish_seconds, templates=templates)
                found.statistics.update(metrics)
                if refined.final_cash > found.result.final_cash:
                    if found.statistics["certified"]:
                        raise RuntimeError("Polishing improved a claimed exact result")
                    found.statistics["best_source"] = "polish"
                found = SearchResult(refined, found.statistics)
                save_record(path, scenario, found.result, found.statistics)
                summary = {"education": scenario.education.value, "job_track": scenario.education.job_track,
                           "starting_bonus": scenario.starting_bonus.value,
                           "starting_bonus_label": scenario.starting_bonus.label,
                           "max_businesses": scenario.max_businesses, "end_month": scenario.end_month,
                           "bonus_years": args.bonus_years,
                           "final_cash": found.result.final_cash, "checkpoint": str(path), **found.statistics}
                with (args.output_dir / "attempts.jsonl").open("a") as stream:
                    stream.write(json.dumps(summary) + "\n")
                if args.json:
                    print(json.dumps(summary), flush=True)
                else:
                    print(f"{scenario.education.label}/{scenario.starting_bonus.label}: ${found.result.final_cash:,.2f}; "
                          f"{found.statistics['status']}; {found.statistics['elapsed_seconds']:.2f}s; "
                          f"{found.statistics['peak_rss_kb'] / 1024:.1f} MB; "
                          f"certified={found.statistics['certified']}", flush=True)
                if best is None or found.result.final_cash > best[1].final_cash:
                    best = (scenario, found.result)
            if not args.json:
                print_route(*best)
    except (ValueError, RuntimeError, OSError) as error:
        parser.exit(2, f"Search stopped: {error}\nPreviously written checkpoints remain available.\n")


if __name__ == "__main__":
    main()
