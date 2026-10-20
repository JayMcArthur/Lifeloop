"""Bounded beam search; returns the best replayable strategy it finds."""

from dataclasses import dataclass, replace
from functools import cache
from heapq import nlargest

from .model import (
    BOOST_MONTHS, BUSINESSES, Action, ActionKind, Result, Scenario, State,
    activate, finish, job_payment, trade,
)


@dataclass(slots=True)
class Path:
    actions: tuple[Action, ...]
    previous: "Path | None"


@dataclass(slots=True)
class Node:
    state: State
    path: Path | None


def boost_choices(state: State, month: int):
    choices = [(state, ())]
    if not state.job_until:
        action = Action(month, ActionKind.JOB_BOOST)
        choices.append((activate(state, action), (action,)))
    # Boosting before any businesses are owned wastes the first payment.
    if not state.business_until and state.owned:
        action = Action(month, ActionKind.BUSINESS_BOOST)
        choices += [(activate(choice, action), (*actions, action)) for choice, actions in choices[:]]
    return choices


def trade_choices(scenario: Scenario, state: State, month: int, businesses):
    yield state, ()
    if len(state.owned) < scenario.max_businesses:
        for index, business in enumerate(businesses):
            if state.cash >= business.cost:
                action = Action(month, ActionKind.BUY, index)
                yield trade(scenario, state, action, businesses), (action,)

    for owned in sorted(set(state.owned)):
        sale = Action(month, ActionKind.SELL, owned)
        sold = trade(scenario, state, sale, businesses)
        for index, business in enumerate(businesses):
            if business.income > businesses[owned].income and sold.cash >= business.cost:
                purchase = Action(month, ActionKind.BUY, index)
                yield trade(scenario, sold, purchase, businesses), (sale, purchase)

        if not state.refund_used:
            sale = Action(month, ActionKind.REFUND_BOOST, owned)
            sold = trade(scenario, state, sale, businesses)
            yield sold, (sale,)
            for index, business in enumerate(businesses):
                if sold.cash >= business.cost:
                    purchase = Action(month, ActionKind.BUY, index)
                    yield trade(scenario, sold, purchase, businesses), (sale, purchase)


def solve(scenario: Scenario, beam_width: int = 64, businesses=BUSINESSES) -> Result:
    if beam_width < 1:
        raise ValueError("Beam width must be positive")

    first_month = scenario.education.start_month + 1
    end = scenario.end_month
    payments = [job_payment(scenario.education, month) * scenario.job_multiplier for month in range(end)]
    prefix = [0]
    for payment in payments:
        prefix.append(prefix[-1] + payment)

    @cache
    def owned_values(owned):
        rate = sum(businesses[i].income for i in owned) * scenario.business_multiplier
        resale = sum(businesses[i].refund() for i in owned)
        extra_refund = max((businesses[i].refund(True) - businesses[i].refund() for i in owned), default=0)
        return rate, resale, extra_refund

    beam = [Node(State(cash=scenario.starting_cash), None)]
    for month in range(first_month, end):
        candidates = {}
        for node in beam:
            rate, _, _ = owned_values(node.state.owned)
            for boosted, boost_actions in boost_choices(node.state, month):
                monthly_income = payments[month] * (2 if month < boosted.job_until else 1)
                monthly_income += rate * (2 if month < boosted.business_until else 1)
                paid = replace(boosted, cash=boosted.cash + monthly_income)
                for state, trades in trade_choices(scenario, paid, month, businesses):
                    # For identical holdings and boost clocks, more cash dominates.
                    key = (state.owned, state.job_until, state.business_until, state.refund_used)
                    prior = candidates.get(key)
                    if prior is None or state.cash > prior.state.cash:
                        actions = boost_actions + trades
                        path = Path(actions, node.path) if actions else node.path
                        candidates[key] = Node(state, path)

        next_month = month + 1
        remaining = end - next_month

        def score(node):
            state = node.state
            rate, resale, extra_refund = owned_values(state.owned)
            value = state.cash + resale + rate * remaining
            if not state.refund_used:
                value += extra_refund
            # Estimate holding current businesses to the end, including boosts.
            business_months = min(BOOST_MONTHS, remaining) if not state.business_until else max(
                0, min(state.business_until, end) - next_month)
            value += rate * business_months
            if not state.job_until:
                # Pay only increases: the last available window is the best if waiting.
                value += prefix[end] - prefix[max(next_month, end - BOOST_MONTHS)]
            else:
                value += prefix[max(next_month, min(state.job_until, end))] - prefix[next_month]
            return value

        beam = nlargest(beam_width, candidates.values(), key=score)

    best = max(beam, key=lambda node: finish(scenario, node.state, (), businesses).final_cash)
    segments = []
    path = best.path
    while path is not None:
        segments.append(path.actions)
        path = path.previous
    actions = tuple(action for segment in reversed(segments) for action in segment)
    return finish(scenario, best.state, actions, businesses)
