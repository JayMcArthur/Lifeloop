import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lifeloop.model import Education, Scenario, StartingBonus
from lifeloop.records import load_record
from lifeloop.solver import ROOT


class RecordedStrategyTests(unittest.TestCase):
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
