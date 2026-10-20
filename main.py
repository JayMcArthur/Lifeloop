"""Run the LifeLoop strategy search in the repository's pinned environment."""

import argparse

from lifeloop.model import BUSINESSES, ActionKind, Education, Scenario, StartingBonus, age, replay
from lifeloop.solver import solve


def main():
    parser = argparse.ArgumentParser(description="Find a LifeLoop strategy using bounded beam search.")
    parser.add_argument("--education", choices=[e.value for e in Education], default="docudyno")
    parser.add_argument("--starting-bonus", choices=[b.value for b in StartingBonus], default="business")
    parser.add_argument("--beam-width", type=int, default=64, help="states retained each month (default: 64)")
    args = parser.parse_args()
    if args.beam_width < 1:
        parser.error("--beam-width must be positive")
    scenario = Scenario(Education(args.education), StartingBonus(args.starting_bonus))
    result = solve(scenario, args.beam_width)
    if replay(scenario, result.actions) != result:
        raise RuntimeError("Strategy replay does not match the search result")

    print(f"Education: {scenario.education.value}; starting bonus: +100% {scenario.starting_bonus.value} income")
    print(f"Age {age(scenario.education.start_month)} to {age(scenario.end_month)}; {scenario.max_businesses} business slots")
    print(f"Best strategy found (beam width {args.beam_width}; no global optimality guarantee):")
    for action in (*result.actions, *result.final_sales):
        detail = BUSINESSES[action.business].name if action.business is not None else "for 120 payments"
        if action.kind in (ActionKind.SELL, ActionKind.REFUND_BOOST):
            refund = BUSINESSES[action.business].refund(action.kind == ActionKind.REFUND_BOOST)
            detail += f" → ${refund:,}"
        print(f"{age(action.month)}: {action.kind.value} {detail}")
    print(f"Final cash after business refunds: ${result.final_cash:,}")


if __name__ == "__main__":
    main()
