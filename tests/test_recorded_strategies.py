import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lifeloop.model import Education, Scenario, StartingBonus
from lifeloop.records import load_record
from lifeloop.solver import ROOT


class RecordedStrategyTests(unittest.TestCase):
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
                floor = load_record(ROOT / "benchmarks/bonus-comparison/records" / name, scenario)
                saved = load_record(Path(directory) / name, scenario)
                self.assertEqual(saved.final_cash, summary["final_cash"])
                self.assertGreaterEqual(saved.final_cash, floor.final_cash)

    def test_primary_cli_selects_primary_education_and_freshmart_job_track(self):
        scenario = Scenario(Education.PRIMARY)
        floor = load_record(ROOT / "benchmarks/records/primary-business.json", scenario)
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

    def test_all_published_reference_and_comparison_scores_pass_independent_replay(self):
        sets = (("benchmarks/records", (StartingBonus.JOB, StartingBonus.BUSINESS)),
                ("benchmarks/bonus-comparison/records", (StartingBonus.JOB, StartingBonus.BUSINESS_50)))
        for directory, bonuses in sets:
            for education in Education:
                for bonus in bonuses:
                    with self.subTest(directory=directory, education=education, bonus=bonus):
                        # Loading checks signatures and independently replays scores.
                        load_record(ROOT / directory / f"{education.value}-{bonus.value}.json",
                                    Scenario(education, bonus))

    def test_fresh_output_directory_keeps_committed_default_strategy(self):
        scenario = Scenario()
        floor = load_record(ROOT / "benchmarks/records/university-business.json", scenario)
        baseline = load_record(ROOT / "benchmarks/records/python-baseline.json", scenario)
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
