import json
import unittest
from dataclasses import FrozenInstanceError

from observer.inspector import render_inspector
from scenarios.first_day import (
    RATION_SCHEDULE_ARTIFACT_ID,
    RATION_SCHEDULE_PERIOD_ID,
    RATION_SCHEDULE_VERSION_ONE_ID,
    build_first_day,
)


class OfficialRecordTests(unittest.TestCase):
    def test_initial_publication_sets_current_three_packet_weekly_version(self):
        simulation = build_first_day(seed=42)

        self.assertEqual(simulation.world.institution.official_record.versions, ())

        simulation.step()

        record = simulation.world.institution.official_record
        version = record.current_version
        self.assertIsNotNone(version)
        self.assertEqual(record.artifact_id, RATION_SCHEDULE_ARTIFACT_ID)
        self.assertEqual(record.current_version_id, RATION_SCHEDULE_VERSION_ONE_ID)
        self.assertEqual(record.versions, (version,))
        self.assertEqual(version.artifact_id, RATION_SCHEDULE_ARTIFACT_ID)
        self.assertEqual(version.version_id, RATION_SCHEDULE_VERSION_ONE_ID)
        self.assertEqual(version.period_id, RATION_SCHEDULE_PERIOD_ID)
        self.assertEqual(version.entitlement_packets, 3)
        self.assertIsNone(version.previous_version_id)

        publication = next(
            event
            for event in simulation.events
            if event.kind == "official_record_published"
        )
        self.assertEqual(publication.actor_id, "civic-allocation-office")
        self.assertEqual(publication.tick, 1)
        self.assertEqual(
            dict(publication.details),
            {
                "artifact_id": RATION_SCHEDULE_ARTIFACT_ID,
                "version_id": RATION_SCHEDULE_VERSION_ONE_ID,
                "period_id": RATION_SCHEDULE_PERIOD_ID,
                "entitlement_packets": 3,
                "previous_version_id": None,
            },
        )
        history = simulation.history_data()
        self.assertFalse(
            any(
                observation["event_id"] == publication.event_id
                for observation in history["observations"]
            )
        )

        detached = record.to_data()
        self.assertEqual(history["official_record"], detached)
        inspector_lines = render_inspector(simulation).splitlines()
        inspector_payload = json.loads("\n".join(inspector_lines[2:]))
        self.assertEqual(inspector_payload["official_record"], detached)

        with self.assertRaises(FrozenInstanceError):
            version.entitlement_packets = 99
        with self.assertRaises(AttributeError):
            record.artifact_id = "replacement-artifact"
        detached["versions"][0]["entitlement_packets"] = 99
        self.assertEqual(record.current_version.entitlement_packets, 3)


if __name__ == "__main__":
    unittest.main()
