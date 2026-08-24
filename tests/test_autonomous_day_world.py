import unittest

from scenarios.autonomous_day import ILAN_ID, MARA_ID, build_autonomous_day


class AutonomousDayWorldTests(unittest.TestCase):
    def test_supporting_work_and_institution_continue_while_mara_is_inactive(self):
        day = build_autonomous_day(seed=42)

        summary = day.run()

        self.assertTrue(summary.reached_end_boundary)
        self.assertTrue(day.runtime.is_complete)
        self.assertEqual(summary.current.total_minutes, 1440)
        self.assertEqual(day.world.tick, 1440)
        self.assertEqual(
            [(event.tick, event.kind, event.actor_id) for event in day.events],
            [
                (480, "action_attempted", ILAN_ID),
                (510, "transit_service_changed", "district-transit-authority"),
                (600, "work_completed", ILAN_ID),
            ],
        )
        attempted, transit_change, completed = day.events
        self.assertEqual(completed.caused_by, (attempted.event_id,))
        self.assertEqual(completed.action_id, attempted.action_id)
        self.assertEqual(transit_change.details["prior_status"], "normal")
        self.assertEqual(transit_change.details["current_status"], "reduced")
        self.assertEqual(day.world.institution.records["tram_service"], "reduced")

        ilan = day.world.agents[ILAN_ID]
        self.assertEqual([attempt.kind for attempt in ilan.action_history], ["work"])
        self.assertEqual([result.status for result in ilan.action_results], ["completed"])
        self.assertEqual(day.pending_action_count, 0)

        mara = day.world.agents[MARA_ID]
        self.assertEqual(mara.location, "home")
        self.assertEqual(mara.action_history, [])
        self.assertEqual(mara.action_results, [])
        self.assertEqual(mara.observations, [])
        self.assertEqual(day.observations, ())
        self.assertEqual(summary.to_data()["decision_counts_by_actor"], {MARA_ID: 0})

    def test_equal_seed_builds_equal_ordered_world_evidence(self):
        first = build_autonomous_day(seed=7)
        second = build_autonomous_day(seed=7)

        first_summary = first.run().to_data()
        second_summary = second.run().to_data()

        self.assertEqual(first.events, second.events)
        self.assertEqual(first_summary, second_summary)
        self.assertEqual(first.world.institution.records, second.world.institution.records)
        self.assertEqual(
            first.world.agents[ILAN_ID].action_results,
            second.world.agents[ILAN_ID].action_results,
        )


if __name__ == "__main__":
    unittest.main()
