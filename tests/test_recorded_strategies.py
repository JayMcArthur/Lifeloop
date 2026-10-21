import json
from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
import unittest

from lifeloop.model import Education, Scenario, StartingBonus, replay
from lifeloop.records import load_record
from lifeloop.solver import ROOT
from main import print_route


class RecordedStrategyTests(unittest.TestCase):
    def test_ten_slot_saved_guides_replay_for_both_horizons(self):
        for years in (90, 95):
            directory = ROOT / "benchmarks/business-10" / f"age-{years}"
            for education in Education:
                with self.subTest(years=years, education=education):
                    scenario = Scenario(education, max_businesses=10, end_month=years * 12)
                    name = f"{education.value}-business"
                    result = load_record(directory / "records" / f"{name}.json", scenario)
                    previous = load_record(ROOT / "benchmarks/current/records" / f"{name}.json",
                                           Scenario(education, max_businesses=9))
                    self.assertGreaterEqual(result.final_cash, replay(scenario, previous.actions).final_cash)
                    self.assertTrue(all(a.month < scenario.end_month
                                        for a in (*result.actions, *result.final_sales)))
                    output = io.StringIO()
                    with redirect_stdout(output):
                        print_route(scenario, result)
                    self.assertEqual((directory / "strategies" / f"{name}.txt").read_text(), output.getvalue())
                    if years == 90:
                        self.assertEqual((ROOT / "benchmarks/strategies" / f"{name}.txt").read_text(),
                                         output.getvalue())

    def test_cli_explicit_nine_slots_can_reproduce_the_previous_scenario(self):
        scenario = Scenario(Education.PRIMARY, max_businesses=9)
        floor = load_record(ROOT / "benchmarks/current/records/primary-business.json", scenario)
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run([str(ROOT / "scripts/run_safe.sh"), "--education", "primary",
                                        "--max-businesses", "9", "--beam-width", "1", "--seconds", "1",
                                        "--polish-seconds", "0", "--json", "--output-dir", directory],
                                       cwd=ROOT, capture_output=True, text=True, check=True, timeout=30)
            summary = json.loads(completed.stdout)
            self.assertEqual(summary["max_businesses"], 9)
            saved = load_record(Path(directory) / "primary-business.json", scenario)
            self.assertGreaterEqual(saved.final_cash, floor.final_cash)

    def test_comparison_cli_selects_only_current_bonuses_and_keeps_saved_floors(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run([str(ROOT / "scripts/run_safe.sh"), "--compare-starting-bonuses",
                                        "--beam-width", "1", "--seconds", "1", "--polish-seconds", "0",
                                        "--json", "--output-dir", directory], cwd=ROOT, capture_output=True,
                                       text=True, check=True, timeout=30)
            summaries = [json.loads(line) for line in completed.stdout.splitlines()]
            expected = {(e.value, b.value) for e in Education
                        for b in (StartingBonus.JOB, StartingBonus.BUSINESS_50)}
            self.assertEqual({(s["education"], s["starting_bonus"]) for s in summaries}, expected)
            self.assertEqual(len(summaries), 10)
            for summary in summaries:
                scenario = Scenario(Education(summary["education"]), StartingBonus(summary["starting_bonus"]))
                name = f"{scenario.education.value}-{scenario.starting_bonus.value}.json"
                old = Scenario(scenario.education, scenario.starting_bonus, max_businesses=9)
                floor = load_record(ROOT / "benchmarks/current/records" / name, old)
                slots = 9 if scenario.starting_bonus == StartingBonus.JOB else 10
                scenario = Scenario(scenario.education, scenario.starting_bonus, max_businesses=slots)
                saved = load_record(Path(directory) / name, scenario)
                self.assertEqual(summary["max_businesses"], slots)
                self.assertEqual(summary["end_month"], 90 * 12)
                self.assertEqual(summary["bonus_years"], 0)
                self.assertEqual(saved.final_cash, summary["final_cash"])
                self.assertGreaterEqual(saved.final_cash, floor.final_cash)

    def test_primary_cli_selects_primary_education_and_freshmart_job_track(self):
        scenario = Scenario(Education.PRIMARY)
        floor = load_record(ROOT / "benchmarks/current/records/primary-business.json",
                            Scenario(Education.PRIMARY, max_businesses=9))
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run([str(ROOT / "scripts/run_safe.sh"), "--education", "primary",
                                        "--beam-width", "1", "--seconds", "1", "--polish-seconds", "0",
                                        "--json", "--output-dir", directory], cwd=ROOT, capture_output=True,
                                       text=True, check=True, timeout=30)
            summary = json.loads(completed.stdout)
            self.assertEqual(summary["education"], "primary")
            self.assertEqual(summary["job_track"], "FreshMart")
            saved = load_record(Path(directory) / "primary-business.json", scenario)
            self.assertGreaterEqual(saved.final_cash, floor.final_cash)

    def test_current_scores_replay_and_historical_rule_checkpoints_are_rejected(self):
        for education in Education:
            for bonus in StartingBonus:
                scenario = Scenario(education, bonus, max_businesses=9)
                with self.subTest(education=education, bonus=bonus):
                    result = load_record(ROOT / "benchmarks/current/records" /
                                         f"{education.value}-{bonus.value}.json", scenario)
                    self.assertTrue(all(a.month < scenario.end_month
                                        for a in (*result.actions, *result.final_sales)))
        with self.assertRaisesRegex(ValueError, "different scenario or rule set"):
            load_record(ROOT / "benchmarks/records/university-business.json", Scenario())

    def test_fresh_output_directory_keeps_committed_default_strategy(self):
        scenario = Scenario()
        old = Scenario(max_businesses=9)
        floor = load_record(ROOT / "benchmarks/current/records/university-business.json", old)
        baseline = load_record(ROOT / "benchmarks/current/records/python-baseline.json", old)
        self.assertGreater(floor.final_cash, baseline.final_cash)
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run([str(ROOT / "scripts/run_safe.sh"), "--beam-width", "1",
                                        "--seconds", "1", "--polish-seconds", "0", "--json",
                                        "--output-dir", directory], cwd=ROOT, capture_output=True,
                                       text=True, check=True, timeout=30)
            summary = json.loads(completed.stdout)
            self.assertGreaterEqual(summary["final_cash"], floor.final_cash)
            saved = load_record(Path(directory) / "university-business.json", scenario)
            self.assertEqual(saved.final_cash, summary["final_cash"])

    def test_cli_optional_extension_replays_old_floor_with_new_horizon_and_slots(self):
        old = Scenario(Education.PRIMARY, max_businesses=9)
        old_route = load_record(ROOT / "benchmarks/current/records/primary-business.json", old)
        scenario = Scenario(Education.PRIMARY, max_businesses=10, end_month=95 * 12)
        floor = replay(scenario, old_route.actions)
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run([str(ROOT / "scripts/run_safe.sh"), "--education", "primary",
                                        "--bonus-years", "5", "--beam-width", "1", "--seconds", "1",
                                        "--polish-seconds", "0", "--json", "--output-dir", directory],
                                       cwd=ROOT, capture_output=True, text=True, check=True, timeout=30)
            summary = json.loads(completed.stdout)
            self.assertEqual(summary["max_businesses"], 10)
            self.assertEqual(summary["end_month"], 95 * 12)
            self.assertEqual(summary["bonus_years"], 5)
            saved = load_record(Path(directory) / "primary-business.json", scenario)
            self.assertGreaterEqual(saved.final_cash, floor.final_cash)
            with self.assertRaisesRegex(ValueError, "different scenario"):
                load_record(Path(directory) / "primary-business.json", old)
