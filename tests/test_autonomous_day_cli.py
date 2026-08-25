import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout

from scenarios.autonomous_day import main


class AutonomousDayCliTests(unittest.TestCase):
    def test_module_command_runs_exact_day_with_focal_safe_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "scenarios.autonomous_day", "--seed", "42"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("Start: Day 0 00:00 | Mara at Home", result.stdout)
        self.assertIn(
            "Day 0 00:00–Day 0 11:00 | No focal updates.", result.stdout
        )
        self.assertIn("Day 0 11:00 | Home transit bulletin", result.stdout)
        self.assertIn(
            "Day 0 11:00–Day 1 00:00 | No focal updates.", result.stdout
        )
        self.assertIn("End: Day 1 00:00", result.stdout)
        self.assertIn("Exact 24-hour boundary reached: yes", result.stdout)
        for hidden in (
            "Ilan",
            "transit_service_changed",
            "action_attempted",
            "work_completed",
            "event-",
            "executed_work",
            "district-transit-authority",
            "peak_restricted_input_bytes",
            "retained_private_record",
        ):
            self.assertNotIn(hidden, result.stdout)

    def test_equal_seed_produces_equal_normal_output(self):
        outputs = []
        for _ in range(2):
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["--seed", "7"])
            self.assertEqual(exit_code, 0)
            outputs.append(output.getvalue())

        self.assertEqual(outputs[0], outputs[1])

    def test_inspector_is_explicit_and_reconstructs_successful_day(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scenarios.autonomous_day",
                "--seed",
                "42",
                "--inspect",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            result.stdout.startswith(
                "2084 AUTONOMOUS DAY INSPECTOR — OMNISCIENT\n"
                "Not part of the normal observer experience.\n"
            )
        )
        data = json.loads(result.stdout[result.stdout.index("{"):])
        self.assertEqual(data["counts"], {
            "action_results": 1,
            "events": 3,
            "observations": 1,
        })
        self.assertEqual(data["model_path"], {
            "configured": False,
            "decision_status_counts": None,
            "exercised": False,
            "provider_failure_count": None,
            "growth": None,
        })
        self.assertEqual(data["objective_state"]["tick"], 1440)
        self.assertEqual(
            [item["kind"] for item in data["history"]["events"]],
            ["action_attempted", "transit_service_changed", "work_completed"],
        )
        attempted, transit, completed = data["history"]["events"]
        self.assertEqual(completed["caused_by"], [attempted["event_id"]])
        self.assertEqual(
            data["history"]["observations"][0]["event_id"],
            transit["event_id"],
        )
        self.assertEqual(
            data["history"]["action_results"][0]["outcome_event_id"],
            completed["event_id"],
        )
        self.assertEqual(data["runtime"]["executed_work_count"], 5)
        self.assertEqual(
            [item["kind"] for item in data["runtime"]["executed_work"]],
            [
                "autonomous_day_supporting_work_start",
                "autonomous_day_institutional_service_change",
                "autonomous_day_supporting_work_completion",
                "autonomous_day_transit_bulletin_delivery",
                "autonomous_day_mara_transit_understanding_update",
            ],
        )
        self.assertEqual(data["runtime"]["quiet_span_count"], 5)
        self.assertTrue(data["runtime"]["reached_end_boundary"])

    def test_invalid_seed_is_controlled_before_world_construction(self):
        result = subprocess.run(
            [sys.executable, "-m", "scenarios.autonomous_day", "--seed", "invalid"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid int value", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
