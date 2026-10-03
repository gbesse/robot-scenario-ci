import json
from pathlib import Path
import tempfile
import unittest

from reset_ledger import ResetLedger, compare, inspect


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def load(name):
    return [json.loads(line) for line in (FIXTURES / name).read_text().splitlines()]


class FakeEnvironment:
    def __init__(self):
        self.state = 0

    def reset(self, *, seed=None):
        self.state += 1
        return {"state": self.state}

    def step(self):
        self.reset()


class ResetLedgerTests(unittest.TestCase):
    def test_matched_initial_states_allow_different_outcomes(self):
        for locale in ("fr", "en", "es"):
            report = compare(load("reset-run-a.jsonl"), load("reset-run-b.jsonl"), locale)
            self.assertEqual(report["status"], "pass")

    def test_internal_reset_is_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resets.jsonl"
            env = FakeEnvironment()
            ledger = ResetLedger(env, path, lambda result: str(result["state"]), environment_revision="world-v1", simulator_version="sim-1")
            ledger.install()
            ledger.begin_episode("1")
            env.reset(seed=1)
            env.step()
            ledger.end_episode("failure")
            ledger.restore()
            self.assertEqual(inspect([json.loads(line) for line in path.read_text().splitlines()])["status"], "fail")
            self.assertEqual(env.reset()["state"], 3)

    def test_drift_report(self):
        report = compare(load("reset-run-a.jsonl"), load("reset-run-drift.jsonl"))
        self.assertEqual(report["status"], "fail")
        self.assertIn("reset_count", {item["code"] for item in report["findings"]})
        self.assertIn("state", {item["code"] for item in report["findings"]})

    def test_empty_ledger_is_invalid(self):
        with self.assertRaises(ValueError):
            inspect([])


if __name__ == "__main__":
    unittest.main()
