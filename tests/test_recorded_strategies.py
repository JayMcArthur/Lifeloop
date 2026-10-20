import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lifeloop.model import Education, Scenario, StartingBonus
from lifeloop.records import load_record
from lifeloop.solver import ROOT


class RecordedStrategyTests(unittest.TestCase):
    def test_all_ten_published_scores_pass_independent_replay(self):
        for education in Education:
            for bonus in StartingBonus:
                with self.subTest(education=education, bonus=bonus):
                    # The loader checks the rule signature and independently
                    # replays the complete path against its published score.
                    load_record(ROOT / "benchmarks/records" / f"{education.value}-{bonus.value}.json",
                                Scenario(education, bonus))

    def test_fresh_output_directory_keeps_committed_default_strategy(self):
        scenario = Scenario()
        floor = load_record(ROOT / "benchmarks/records/docudyno-business.json", scenario)
        baseline = load_record(ROOT / "benchmarks/records/python-baseline.json", scenario)
        self.assertGreater(floor.final_cash, baseline.final_cash)
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run([str(ROOT / "scripts/run_safe.sh"), "--beam-width", "1",
                                        "--seconds", "1", "--polish-seconds", "0", "--json",
                                        "--output-dir", directory], cwd=ROOT, capture_output=True,
                                       text=True, check=True, timeout=30)
            summary = json.loads(completed.stdout)
            self.assertGreaterEqual(summary["final_cash"], floor.final_cash)
            saved = load_record(Path(directory) / "docudyno-business.json", scenario)
            self.assertEqual(saved.final_cash, summary["final_cash"])
