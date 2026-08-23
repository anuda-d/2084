import unittest

from simulation.time import MINUTES_PER_DAY, SimulatedDayClock, SimulatedTime


class SimulatedTimeTests(unittest.TestCase):
    def test_integer_minutes_define_conversion_and_total_order(self):
        midnight = SimulatedTime.from_day_time(
            day_index=0,
            hour=0,
            minute=0,
        )
        before_midnight = SimulatedTime.from_day_time(
            day_index=3,
            hour=23,
            minute=59,
        )
        next_midnight = before_midnight.plus_minutes(1)

        self.assertEqual(midnight.total_minutes, 0)
        self.assertEqual(midnight.label, "Day 0 00:00")
        self.assertLess(before_midnight, next_midnight)
        self.assertEqual(next_midnight.label, "Day 4 00:00")
        self.assertEqual(
            next_midnight.to_data(),
            {
                "total_minutes": 4 * MINUTES_PER_DAY,
                "day_index": 4,
                "hour": 0,
                "minute": 0,
                "label": "Day 4 00:00",
            },
        )

    def test_non_midnight_start_ends_exactly_twenty_four_hours_later(self):
        start = SimulatedTime.from_day_time(
            day_index=7,
            hour=6,
            minute=30,
        )
        clock = SimulatedDayClock(start)

        self.assertEqual(clock.current, start)
        self.assertEqual(clock.advance_to(start), start)
        self.assertEqual(clock.end.total_minutes - start.total_minutes, 1_440)
        self.assertEqual(clock.end.label, "Day 8 06:30")
        self.assertFalse(clock.is_complete)
        clock.advance_by(1_439)
        self.assertFalse(clock.is_complete)
        clock.advance_by(1)
        self.assertTrue(clock.is_complete)
        self.assertEqual(clock.current, clock.end)
        self.assertTrue(clock.to_data()["reached_end_boundary"])

    def test_clock_refuses_backward_and_beyond_boundary_advancement(self):
        start = SimulatedTime.from_day_time(
            day_index=0,
            hour=8,
            minute=0,
        )
        clock = SimulatedDayClock(start)
        clock.advance_by(90)

        with self.assertRaisesRegex(ValueError, "cannot move backward"):
            clock.advance_to(start.plus_minutes(89))
        self.assertEqual(clock.current, start.plus_minutes(90))
        with self.assertRaisesRegex(ValueError, "beyond the day boundary"):
            clock.advance_to(clock.end.plus_minutes(1))
        self.assertEqual(clock.current, start.plus_minutes(90))

    def test_invalid_components_and_durations_are_rejected(self):
        invalid_constructors = (
            lambda: SimulatedTime(-1),
            lambda: SimulatedTime.from_day_time(
                day_index=-1,
                hour=0,
                minute=0,
            ),
            lambda: SimulatedTime.from_day_time(
                day_index=0,
                hour=24,
                minute=0,
            ),
            lambda: SimulatedTime.from_day_time(
                day_index=0,
                hour=0,
                minute=60,
            ),
            lambda: SimulatedTime.from_day_time(
                day_index=0,
                hour=True,
                minute=0,
            ),
        )
        for constructor in invalid_constructors:
            with self.subTest(constructor=constructor):
                with self.assertRaises(ValueError):
                    constructor()

        clock = SimulatedDayClock(SimulatedTime(0))
        with self.assertRaises(ValueError):
            clock.advance_by(-1)


if __name__ == "__main__":
    unittest.main()
