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
Reason: handover observation-0004 granted 1 of 3 needed, leaving 2 units.
Delivered at tick 4 via direct allocation outcome: 0 units granted; 2 units unfilled.
Social pressure delivered at tick 4 via supporting person: urge public agreement.
Remaining-need constraint: 2 units from follow-up outcome observation-0005.
Decision: seek alternative source.
Reason: follow-up outcome observation-0005 granted 0 units and left 2 units unfilled; pressure observation-0006 said urge public agreement; rule: wait without a delivered follow-up outcome; otherwise use the latest outcome shortfall as remaining need, seek an alternative source when matching social pressure was delivered, wait for changed conditions while need remains, or continue ordinary task.
Resolved at tick 5 via direct alternative-source result: 1 unit granted; 1 unit unfilled.
Private belief: 2 units available from direct observation observation-0001.
Public expression: 4 units available.
Reason: pressure observation-0006 urged public agreement, so official claim observation-0002 was repeated while the private belief remained unchanged.
Diary write (private perspective): started at tick 6 and completed at tick 7; retained 2 units available.
Diary read at tick 8: returned the same retained private entry, 2 units available.
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
