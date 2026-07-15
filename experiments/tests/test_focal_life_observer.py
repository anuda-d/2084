import subprocess
import sys
import unittest

from experiments.focal_life_observer import render_focal_life_transcript
from experiments.focal_life_scenario import run_provisional_focal_life_scenario


EXPECTED_TRANSCRIPT = """2084 focal-life observer (provisional)
Need: 3 units; request limit: 3 units.
Observed at tick 1 via direct sight [direct]: 2 units available.
Observed at tick 2 via official notice [official claim]: 4 units available.
Decision: request 2 units.
Reason: preferred direct observation observation-0001 (2 units), then capped by need 3 and request limit 3.
Delivered at tick 3 via direct handover: 1 unit granted; 1 unit unfilled.
Decision: seek remaining allocation (2 units).
Reason: handover observation-0003 granted 1 of 3 needed, leaving 2 units.
Delivered at tick 4 via direct allocation outcome: 0 units granted; 2 units unfilled.
"""


class FocalLifeObserverTests(unittest.TestCase):
    def test_fixed_scenario_renders_focal_perspective_transcript(self):
        transcript = render_focal_life_transcript(
            run_provisional_focal_life_scenario()
        )

        self.assertEqual(transcript, EXPECTED_TRANSCRIPT)

    def test_module_command_prints_fixed_scenario_transcript(self):
        completed = subprocess.run(
            [sys.executable, "-m", "experiments.focal_life_observer"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            (completed.returncode, completed.stdout, completed.stderr),
            (0, EXPECTED_TRANSCRIPT, ""),
        )


if __name__ == "__main__":
    unittest.main()
