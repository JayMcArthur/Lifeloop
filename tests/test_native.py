from collections import deque
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lifeloop.model import Action, ActionKind, Business, Education, Scenario, StartingBonus, job_payment, replay
from lifeloop.records import load_record, save_record
from lifeloop.solver import ROOT, ensure_binary, solve


def exhaustive_cash(scenario, businesses):
    """Independent tiny oracle, including arbitrary same-month trade sequences."""
    first = scenario.education.start_month + 1
    frontier = {(tuple(0 for _ in businesses), 0, 0, False): scenario.starting_cash}
    for month in range(first, scenario.end_month):
        paid = {}
        for (owned, job_end, business_end, used), cash in frontier.items():
            for job_now in (False, True) if not job_end else (False,):
                for business_now in (False, True) if not business_end else (False,):
                    j = month + 120 if job_now else job_end
                    b = month + 120 if business_now else business_end
                    earned = job_payment(scenario.education, month) * scenario.job_multiplier * (2 if month < j else 1)
                    earned += sum(n * business.income for n, business in zip(owned, businesses)) * scenario.business_multiplier * (2 if month < b else 1)
                    key = owned, j, b, used
                    paid[key] = max(paid.get(key, -1), cash + earned)
        queue = deque(paid.items())
        while queue:
            key, cash = queue.popleft()
            if paid[key] != cash:
                continue
            owned, j, b, used = key
            for index, business in enumerate(businesses):
                choices = []
                if sum(owned) < scenario.max_businesses and cash >= business.cost:
                    counts = list(owned); counts[index] += 1
                    choices.append(((tuple(counts), j, b, used), cash - business.cost))
                if owned[index]:
                    counts = list(owned); counts[index] -= 1
                    choices.append(((tuple(counts), j, b, used), cash + business.cost * 7 // 10))
                    if not used:
                        choices.append(((tuple(counts), j, b, True), cash + business.cost * 14 // 10))
                for new_key, value in choices:
                    if value > paid.get(new_key, -1):
                        paid[new_key] = value
                        queue.append((new_key, value))
        frontier = paid
    best = 0
    for (owned, _, _, used), cash in frontier.items():
        value = cash + sum(n * b.cost * 7 // 10 for n, b in zip(owned, businesses))
        if not used:
            value += max((b.cost * 7 // 10 for n, b in zip(owned, businesses) if n), default=0)
        best = max(best, value)
    return best


class NativeSearchTests(unittest.TestCase):
    def test_native_matches_exhaustive_unrestricted_tiny_oracle(self):
        businesses = (Business("Small", 100, 30), Business("Large", 200, 55))
        for bonus in StartingBonus:
            for months in (1, 2, 3):
                scenario = Scenario(Education.DOCUDYNO, bonus, 300, 2, 265 + months)
                with self.subTest(bonus=bonus, months=months):
                    found = solve(scenario, 5000, businesses, seconds=5)
                    self.assertEqual(found.result.final_cash, exhaustive_cash(scenario, businesses))
                    self.assertTrue(found.statistics["certified"])

    def test_multiple_purchases_can_happen_in_the_same_month(self):
        businesses = (Business("Shop", 100, 100),)
        scenario = Scenario(starting_cash=900, max_businesses=9, end_month=269)
        found = solve(scenario, 10000, businesses, seconds=5)
        self.assertEqual(found.result.final_cash, exhaustive_cash(scenario, businesses))
        purchases = [a for a in found.result.actions if a.kind == ActionKind.BUY and a.month == 265]
        self.assertGreater(len(purchases), 1)
        self.assertTrue(found.statistics["certified"])

    def test_stopped_search_keeps_replayed_incumbent_and_reports_no_certificate(self):
        scenario = Scenario()
        seed = load_record(ROOT / "benchmarks/records/python-baseline.json", scenario)
        found = solve(scenario, 50000, seconds=1, incumbent=seed)
        self.assertGreaterEqual(found.result.final_cash, seed.final_cash)
        self.assertEqual(found.statistics["status"], "time_limit")
        self.assertFalse(found.statistics["certified"])
        self.assertLessEqual(found.statistics["peak_pool"], 100000)
        self.assertEqual(replay(scenario, found.result.actions), found.result)

    def test_expired_boost_seed_replays_in_native_and_python(self):
        scenario = Scenario(starting_cash=3000, end_month=265 + 125)
        seed = replay(scenario, (Action(265, ActionKind.JOB_BOOST), Action(265, ActionKind.BUY, 0),
                                 Action(266, ActionKind.BUSINESS_BOOST)))
        found = solve(scenario, 16, seconds=1, incumbent=seed)
        self.assertGreaterEqual(found.result.final_cash, seed.final_cash)
        self.assertEqual(replay(scenario, found.result.actions), found.result)
        self.assertLessEqual(found.statistics["peak_pool"], 32)

    def test_checkpoint_roundtrip_and_tampering_rejection(self):
        scenario = Scenario(end_month=267)
        result = replay(scenario, (Action(265, ActionKind.JOB_BOOST),))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "best.json"
            save_record(path, scenario, result, {"test": True})
            original = path.read_bytes()
            self.assertEqual(load_record(path, scenario), result)
            with self.assertRaisesRegex(ValueError, "different scenario"):
                load_record(path, replace(scenario, starting_bonus=StartingBonus.JOB))
            with self.assertRaisesRegex(ValueError, "invalid result"):
                save_record(path, scenario, replace(result, final_cash=result.final_cash + 1), {})
            self.assertEqual(path.read_bytes(), original)
            data = json.loads(original)
            data["result"]["final_cash"] += 1
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "does not match"):
                load_record(path, scenario)


class NativeSafetyTests(unittest.TestCase):
    def test_real_kernel_limits_cover_native_and_nested_jobs(self):
        binary = ensure_binary()
        environment = {**os.environ, "LIMIT_MAX_MB": "256", "LIMIT_MAX_SECONDS": "5"}
        completed = subprocess.run([str(ROOT / "scripts/run_limited.sh"), str(binary), "--safety-report"],
                                   capture_output=True, text=True, env=environment, check=True, timeout=15)
        limits = json.loads(completed.stdout)
        self.assertLessEqual(limits["address_space"], 256 * 1024 * 1024)
        self.assertLessEqual(limits["job_memory"], 1024 * 1024 * 1024)
        self.assertGreater(limits["cpu_seconds"], 0)
        self.assertEqual(limits["core_bytes"], 0)
        self.assertEqual(limits["job_swap"], 0)
        self.assertLessEqual(limits["cpu_quota"], limits["cpu_period"])
        self.assertLessEqual(limits["tasks"], 64)
        self.assertEqual(limits["oom_group"], 1)

    def test_oversize_memory_override_is_rejected_before_command_runs(self):
        completed = subprocess.run([str(ROOT / "scripts/run_limited.sh"), sys.executable, "-c", "print('SHOULD_NOT_RUN')"],
                                   capture_output=True, text=True, env={**os.environ, "LIMIT_MAX_MB": "2048"})
        self.assertEqual(completed.returncode, 2)
        self.assertNotIn("SHOULD_NOT_RUN", completed.stdout)

    def test_timeout_terminates_descendant(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "child.pid"
            code = "import subprocess,time,pathlib; p=subprocess.Popen(['sleep','30']); pathlib.Path(" + repr(str(path)) + ").write_text(str(p.pid)); time.sleep(30)"
            completed = subprocess.run([str(ROOT / "scripts/run_limited.sh"), sys.executable, "-c", code],
                                       capture_output=True, text=True, timeout=12,
                                       env={**os.environ, "LIMIT_MAX_SECONDS": "1"})
            self.assertEqual(completed.returncode, 124)
            pid = int(path.read_text())
            status = Path(f"/proc/{pid}/stat")
            if status.exists():
                self.assertEqual(status.read_text().split()[2], "Z")

    def test_compiler_jobs_are_capped_and_serialized(self):
        code = "import json,resource,time; a=time.monotonic(); time.sleep(.15); print(json.dumps([a,time.monotonic(),resource.getrlimit(resource.RLIMIT_AS)[0]]))"
        command = [str(ROOT / "scripts/compiler_limiter.sh"), sys.executable, "-c", code]
        first = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
        second = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
        a = json.loads(first.communicate(timeout=10)[0])
        b = json.loads(second.communicate(timeout=10)[0])
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertGreaterEqual(max(a[0], b[0]), min(a[1], b[1]))
        self.assertLessEqual(a[2], 768 * 1024 * 1024)
        self.assertLessEqual(b[2], 768 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
