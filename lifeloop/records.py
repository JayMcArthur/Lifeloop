"""Replay-validated, atomic result checkpoints."""

import hashlib
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import tempfile

from .model import BUSINESSES, Action, ActionKind, Scenario, job_payment, replay


@contextmanager
def campaign_lock(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".campaign.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another search owns this output directory") from None
        yield


def scenario_data(scenario: Scenario) -> dict:
    return {"education": scenario.education.value, "starting_bonus": scenario.starting_bonus.value,
            "starting_cash": scenario.starting_cash, "max_businesses": scenario.max_businesses,
            "end_month": scenario.end_month}


def signature(scenario: Scenario, businesses=BUSINESSES) -> str:
    data = {"scenario": scenario_data(scenario),
            "businesses": [(b.name, b.cost, b.income) for b in businesses],
            "payments": [job_payment(scenario.education, m) for m in range(scenario.end_month)],
            "rules": "income-before-trades;boost=120;refund=70/140-once;terminal-no-income;v1"}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def load_record(path: Path, scenario: Scenario, businesses=BUSINESSES):
    data = json.loads(path.read_text())
    if data["schema"] != 1 or data["signature"] != signature(scenario, businesses):
        raise ValueError("Checkpoint belongs to a different scenario or rule set")
    actions = tuple(Action(month, ActionKind(kind), index) for month, kind, index in data["result"]["actions"])
    result = replay(scenario, actions, businesses)
    if result.final_cash != data["result"]["final_cash"]:
        raise ValueError("Checkpoint score does not match replay")
    return result


def save_record(path: Path, scenario: Scenario, result, statistics: dict, businesses=BUSINESSES):
    if replay(scenario, result.actions, businesses) != result:
        raise ValueError("Cannot checkpoint an invalid result")
    data = {"schema": 1, "signature": signature(scenario, businesses), "scenario": scenario_data(scenario),
            "result": {"final_cash": result.final_cash,
                       "actions": [[a.month, a.kind.value, a.business] for a in result.actions]},
            "statistics": statistics}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=path.name + ".", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
