import io
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
        self.assertIn("Day 0 11:00 | Home transit bulletin", result.stdout)
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
