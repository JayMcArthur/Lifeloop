"""Retiming refinement inspired by Caravan's independently replayed route polisher."""

from itertools import groupby
import math
import time

from .model import BUSINESSES, Action, ActionKind, Result, Scenario, job_payment, replay


def polish(scenario: Scenario, incumbent: Result, seconds: float = 5, businesses=BUSINESSES):
    if not math.isfinite(seconds) or seconds < 0 or seconds > 60:
        raise ValueError("Polish budget must be between zero and 60 seconds")
    started = time.monotonic()
    deadline = started + seconds
    best = incumbent
    evaluated = 0
    first, end = scenario.education.start_month + 1, scenario.end_month
    payments = [job_payment(scenario.education, m) * scenario.job_multiplier for m in range(end)]
    starts = {a.kind: a.month for a in best.actions if a.kind in (ActionKind.JOB_BOOST, ActionKind.BUSINESS_BOOST)}
    job_start = starts.get(ActionKind.JOB_BOOST, max(first, end - 120))
    business_start = starts.get(ActionKind.BUSINESS_BOOST, max(first, end - 120))

    def plan(actions, target="current"):
        blocks = []
        sale_id = 0
        for _, events in groupby(actions, key=lambda a: a.month):
            pending = []
            for action in events:
                if action.kind in (ActionKind.JOB_BOOST, ActionKind.BUSINESS_BOOST):
                    continue
                kind = action.kind
                if kind in (ActionKind.SELL, ActionKind.REFUND_BOOST):
                    if target != "current":
                        kind = ActionKind.REFUND_BOOST if sale_id == target else ActionKind.SELL
                    sale_id += 1
                pending.append((kind, action.business))
                if kind == ActionKind.BUY:
                    # A normal sell/rebuy of the same business just burns cash.
                    ordinary = (ActionKind.SELL, action.business)
                    if ordinary in pending:
                        pending.remove(ordinary)
                        pending.pop()
                    if pending:
                        blocks.append(tuple(pending))
                    pending = []
            if pending:
                blocks.append(tuple(pending))
        return blocks, sale_id

    def evaluate(blocks, job, business):
        nonlocal evaluated, best
        evaluated += 1
        cash = scenario.starting_cash
        owned = [0] * len(businesses)
        count = rate = block_index = 0
        used_refund = False
        events = []
        for month in range(first, end):
            if month == job:
                events.append(Action(month, ActionKind.JOB_BOOST))
            if month == business:
                events.append(Action(month, ActionKind.BUSINESS_BOOST))
            cash += payments[month] * (2 if job <= month < job + 120 else 1)
            cash += rate * (2 if business <= month < business + 120 else 1)
            while block_index < len(blocks):
                block = blocks[block_index]
                money, slots, refund_used = cash, count, used_refund
                counts = owned.copy()
                for kind, index in block:
                    item = businesses[index]
                    if kind == ActionKind.BUY:
                        if money < item.cost or slots >= scenario.max_businesses:
                            break
                        money -= item.cost
                        slots += 1
                        counts[index] += 1
                    else:
                        boosted = kind == ActionKind.REFUND_BOOST
                        if not counts[index] or (boosted and refund_used):
                            return
                        counts[index] -= 1
                        slots -= 1
                        money += item.refund(boosted)
                        refund_used = refund_used or boosted
                else:
                    cash, count, owned, used_refund = money, slots, counts, refund_used
                    rate = sum(n * item.income for n, item in zip(owned, businesses)) * scenario.business_multiplier
                    events.extend(Action(month, kind, index) for kind, index in block)
                    block_index += 1
                    continue
                break
        cash += sum(n * item.refund() for n, item in zip(owned, businesses))
        if not used_refund:
            extra = max((item.refund(True) - item.refund() for n, item in zip(owned, businesses) if n), default=0)
            chosen = None
            for index, item in enumerate(businesses):
                gain = item.refund(True) - item.cost
                if first < end and item.cost <= cash and gain > extra:
                    chosen, extra = index, gain
            if chosen is not None:
                events.extend(Action(end - 1, ActionKind.SELL, index)
                              for index, n in enumerate(owned) for _ in range(n))
                events.extend((Action(end - 1, ActionKind.BUY, chosen),
                               Action(end - 1, ActionKind.REFUND_BOOST, chosen)))
            cash += extra
        if cash > best.final_cash:
            result = replay(scenario, tuple(events), businesses)
            if result.final_cash != cash:
                raise RuntimeError("Polish score disagrees with independent replay")
            best = result

    timed_out = False
    while seconds:
        before = best.final_cash
        blocks, sales = plan(best.actions)
        evaluate(blocks, job_start, business_start)
        for kind in (ActionKind.JOB_BOOST, ActionKind.BUSINESS_BOOST):
            for month in range(first, end):
                if time.monotonic() >= deadline:
                    timed_out = True
                    break
                value = best.final_cash
                evaluate(blocks, month if kind == ActionKind.JOB_BOOST else job_start,
                         month if kind == ActionKind.BUSINESS_BOOST else business_start)
                if best.final_cash > value:
                    if kind == ActionKind.JOB_BOOST:
                        job_start = month
                    else:
                        business_start = month
            if timed_out:
                break
        if timed_out:
            break
        for target in [None, *range(sales)]:
            if time.monotonic() >= deadline:
                timed_out = True
                break
            candidate, _ = plan(best.actions, target)
            evaluate(candidate, job_start, business_start)
        if timed_out or best.final_cash == before:
            break
    return best, {"polish_evaluations": evaluated, "polish_elapsed_seconds": time.monotonic() - started,
                  "polish_status": "disabled" if not seconds else "time_limit" if timed_out else "local_fixed_point",
                  "polish_cash_before": incumbent.final_cash, "polish_cash_after": best.final_cash}
