import json
from pathlib import Path
import unittest

from robot_scenario_ci import evaluate, run


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class ScenarioTests(unittest.TestCase):
    def test_synthetic_process(self):
        scenario = json.loads((FIXTURES / "obstacle.json").read_text())
        for locale in ("fr", "en", "es"):
            self.assertEqual(run(scenario, FIXTURES, locale)["status"], "pass")

    def test_missing_stop_fails(self):
        events = [{"at_ms": 0, "event": "obstacle_detected"}, {"at_ms": 100, "event": "goal_reached"}]
        findings = evaluate(events, {"stop_after_obstacle": True, "events": ["goal_reached"]})
        self.assertEqual([item["code"] for item in findings], ["stop"])

    def test_required_event_order(self):
        events = [{"at_ms": 0, "event": "goal_reached"}, {"at_ms": 1, "event": "goal_sent"}]
        findings = evaluate(events, {"events": ["goal_sent", "goal_reached"]})
        self.assertEqual([item["code"] for item in findings], ["sequence"])


if __name__ == "__main__":
    unittest.main()
